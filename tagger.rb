# typed: strict
# frozen_string_literal: true

class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.23.1.tar.gz"
  sha256 "67b0b48f4eefd0b32e1f172432baeb97a3499582cafc09b3b27652a9d19128ad"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "python@3.12"

  # Skip relocation of pydantic_core binary (wheel has insufficient header padding)
  on_arm do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/7b/9e/f8063952e4a7d0127f5d1181addef9377505dcce3be224263b25c4f0bfd9/pydantic_core-2.27.1-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "5f8c4718cd44ec1580e180cb739713ecda2bdee1341084c1467802a417fe0f02"
    end

    resource "pyyaml" do
      url "https://files.pythonhosted.org/packages/a8/0c/38374f5bb272c051e2a69281d71cba6fdb983413e6758b84482905e29a5d/PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "ce826d6ef20b1bc864f0a68340c8b3287705cae2f8b4b1d932177dcc76721725"
    end

    resource "pillow" do
      url "https://files.pythonhosted.org/packages/fd/e0/ed960067543d080691d47d6938ebccbf3976a931c9567ab2fbfab983a5dd/pillow-12.0.0-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "71db6b4c1653045dacc1585c1b0d184004f0d7e694c7b34ac165ca70c0838082"
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

    resource "pillow" do
      url "https://files.pythonhosted.org/packages/2c/90/4fcce2c22caf044e660a198d740e7fbc14395619e3cb1abad12192c0826c/pillow-12.0.0-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "53561a4ddc36facb432fae7a9d8afbfaf94795414f5cdc5fc52f28c1dca90371"
    end
  end

  skip_clean "libexec"

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/18/67/36e9267722cc04a6b9f15c7f3441c2363321a3ea07da7ae0c0707beb2a9c/typing_extensions-4.15.0-py3-none-any.whl"
    sha256 "f0fa19c6845758ab08074a0cfa8b7aecb71c999ca73d62883bc25cc018c4e548"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl"
    sha256 "1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53"
  end

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/b0/7a/620f945b96be1f6ee357d211d5bf74ab1b7fe72a9f1525aafbfe3aee6875/mutagen-1.47.0-py3-none-any.whl"
    sha256 "edd96f50c5907a9539d8e5bba7245f62c9f520aef333d13392a79a4f70aca719"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/62/51/72c18c55cf2f46ff4f91ebcc8f75aa30f7305f3d726be3f4ebffb4ae972b/pydantic-2.10.3-py3-none-any.whl"
    sha256 "be04d85bbc7b65651c5f8e6b9976ed9c6f41782a55524cef079a34a0bb82144d"
  end

  # YouTube thumbnail dependencies
  resource "yt-dlp" do
    url "https://files.pythonhosted.org/packages/6e/2f/98c3596ad923f8efd32c90dca62e241e8ad9efcebf20831173c357042ba0/yt_dlp-2025.12.8-py3-none-any.whl"
    sha256 "36e2584342e409cfbfa0b5e61448a1c5189e345cf4564294456ee509e7d3e065"
  end

  resource "platformdirs" do
    url "https://files.pythonhosted.org/packages/73/cb/ac7874b3e5d58441674fb70742e6c374b28b0c7cb988d37d991cde47166c/platformdirs-4.5.0-py3-none-any.whl"
    sha256 "e578a81bb873cbb89a41fcc904c7ef523cc18284b7e3b3ccf06aca1403b7ebd3"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/a7/c2/fe1e52489ae3122415c51f387e221dd0773709bad6c6cdaa599e8a2c5185/urllib3-2.5.0-py3-none-any.whl"
    sha256 "e6b01673c0fa6a13e374b50871808eb3bf7046c4b125b216f6bf1cc604cff0dc"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/70/7d/9bc192684cea499815ff478dfcdc13835ddf401365057044fb721ec6bddb/certifi-2025.11.12-py3-none-any.whl"
    sha256 "97de8790030bbd5c2d96b7ec782fc2f7820ef8dba6db909ccf95449f2d062d4b"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/0a/4c/925909008ed5a988ccbb72dcc897407e5d6d3bd72410d69e051fc0c14647/charset_normalizer-3.4.4-py3-none-any.whl"
    sha256 "7a32c560861a02ff789ad905a2fe94e3f840803362c84fecf1851cb4cf3dc37f"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/0e/61/66938bbb5fc52dbdf84594873d5b51fb1f7c7794e9c0f5bd885f30bc507b/idna-3.11-py3-none-any.whl"
    sha256 "771a87f49d9defaf64091e6e6fe9c18d4833f140bd19464795bc32d966ca37ea"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/1e/db/4254e3eabe8020b458f1a747140d32277ec7a271daf1d235b70dc0b4e6e3/requests-2.32.5-py3-none-any.whl"
    sha256 "2462f94637a34fd532264295e186976db0f5d453d1cdd31473c85a6a161affb6"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/a0/e3/59cd50310fc9b59512193629e1984c1f95e5c8ae6e5d8c69532ccc65a7fe/pycparser-2.23-py3-none-any.whl"
    sha256 "e5c6e8d3fbad53479cab09ac03729e0a9faf2bee3db8208a550daf5af81a5934"
  end

  def install
    # Create virtualenv
    venv = virtualenv_create(libexec, "python3.12")

    # Install all resources - wheels will be installed directly, tarballs will be built
    resources.each do |r|
      # Install from URL directly to avoid --no-binary issues
      venv.pip_install r.url
    end

    # Install the main package
    venv.pip_install_and_link buildpath

    # Install man pages
    man1.install "man/tagger.1"
    (man/"ja/man1").install "man/ja/tagger.1"

    # Install shell completions
    bash_completion.install "completions/tagger.bash" => "tagger"
    zsh_completion.install "completions/_tagger"
    fish_completion.install "completions/tagger.fish"
  end

  test do
    # Test basic functionality
    system bin/"tagger", "--help"
    system bin/"tagger", "--version"

    # Test YouTube thumbnail dependencies
    # Verify yt-dlp is installed in virtualenv
    system libexec/"bin/python", "-c", "import yt_dlp; " \
           "print('✓ yt-dlp installed correctly')"

    # Verify Pillow is installed in virtualenv
    system libexec/"bin/python", "-c", "from PIL import Image; " \
           "print('✓ Pillow (PIL) installed correctly')"

    # Test man page installation
    assert_predicate man1/"tagger.1", :exist?, "English man page should be installed"
    assert_predicate man/"ja/man1/tagger.1", :exist?, "Japanese man page should be installed"
  end
end
