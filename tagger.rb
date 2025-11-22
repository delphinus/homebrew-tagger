class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.9.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"

  # Optional dependencies for DJ mix segmentation feature
  # Users can install these manually with: pip install librosa numpy

  # Skip relocation of pydantic_core binary (wheel has insufficient header padding)
  skip_clean "libexec"

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/18/67/36e9267722cc04a6b9f15c7f3441c2363321a3ea07da7ae0c0707beb2a9c/typing_extensions-4.15.0-py3-none-any.whl"
    sha256 "f0fa19c6845758ab08074a0cfa8b7aecb71c999ca73d62883bc25cc018c4e548"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl"
    sha256 "1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53"
  end

  on_arm do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/7b/9e/f8063952e4a7d0127f5d1181addef9377505dcce3be224263b25c4f0bfd9/pydantic_core-2.27.1-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "5f8c4718cd44ec1580e180cb739713ecda2bdee1341084c1467802a417fe0f02"
    end

    resource "pyyaml" do
      url "https://files.pythonhosted.org/packages/a8/0c/38374f5bb272c051e2a69281d71cba6fdb983413e6758b84482905e29a5d/PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "ce826d6ef20b1bc864f0a68340c8b3287705cae2f8b4b1d932177dcc76721725"
    end
  end

  on_intel do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/be/51/2e9b3788feb2aebff2aa9dfbf060ec739b38c05c46847601134cc1fed2ea/pydantic_core-2.27.1-cp312-cp312-macosx_10_12_x86_64.whl"
      sha256 "9cbd94fc661d2bab2bc702cddd2d3370bbdcc4cd0f8f57488a81bcce90c7a54f"
    end

    resource "pyyaml" do
      url "https://files.pythonhosted.org/packages/86/0c/c581167fc46d6d6d7ddcfb8c843a4de25bdd27e4466938109ca68492292c/PyYAML-6.0.2-cp312-cp312-macosx_10_9_x86_64.whl"
      sha256 "c70c95198c015b85feafc136515252a261a84561b7b1d51e3384e0655ddf25ab"
    end
  end

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/b0/7a/620f945b96be1f6ee357d211d5bf74ab1b7fe72a9f1525aafbfe3aee6875/mutagen-1.47.0-py3-none-any.whl"
    sha256 "edd96f50c5907a9539d8e5bba7245f62c9f520aef333d13392a79a4f70aca719"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/62/51/72c18c55cf2f46ff4f91ebcc8f75aa30f7305f3d726be3f4ebffb4ae972b/pydantic-2.10.3-py3-none-any.whl"
    sha256 "be04d85bbc7b65651c5f8e6b9976ed9c6f41782a55524cef079a34a0bb82144d"
  end

  def install
    # Create virtualenv and install all wheel resources directly
    venv = virtualenv_create(libexec, "python3.12")

    # Install all wheels directly from URLs
    resources.each do |r|
      venv.pip_install r.url
    end

    # Rewrite shebang in tagger script to use virtualenv python
    inreplace "tagger", %r{^#!/usr/bin/env python3$}, "#!#{libexec}/bin/python"

    # Install tagger script
    bin.install "tagger"

    # Install segmenter module to the virtualenv
    venv.pip_install_and_link buildpath/"segmenter.py"
  end

  test do
    system bin/"tagger", "--help"
  end
end
