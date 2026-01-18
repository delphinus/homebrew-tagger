# typed: strict
# frozen_string_literal: true

class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.25.3.tar.gz"
  sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "python@3.12"

  # Skip relocation of pydantic_core binary (wheel has insufficient header padding)
  on_arm do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/7b/9e/f8063952e4a7d0127f5d1181addef9377505dcce3be224263b25c4f0bfd9/pydantic_core-2.27.1-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end

    resource "pyyaml" do
      url "https://files.pythonhosted.org/packages/a8/0c/38374f5bb272c051e2a69281d71cba6fdb983413e6758b84482905e29a5d/PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end

    resource "pillow" do
      url "https://files.pythonhosted.org/packages/fd/e0/ed960067543d080691d47d6938ebccbf3976a931c9567ab2fbfab983a5dd/pillow-12.0.0-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end
  end

  on_intel do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/be/51/2e9b3788feb2aebff2aa9dfbf060ec739b38c05c46847601134cc1fed2ea/pydantic_core-2.27.1-cp312-cp312-macosx_10_12_x86_64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end

    resource "pyyaml" do
      url "https://files.pythonhosted.org/packages/86/0c/c581167fc46d6d6d7ddcfb8c843a4de25bdd27e4466938109ca68492292c/PyYAML-6.0.2-cp312-cp312-macosx_10_9_x86_64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end

    resource "pillow" do
      url "https://files.pythonhosted.org/packages/2c/90/4fcce2c22caf044e660a198d740e7fbc14395619e3cb1abad12192c0826c/pillow-12.0.0-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
    end
  end

  skip_clean "libexec"

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/18/67/36e9267722cc04a6b9f15c7f3441c2363321a3ea07da7ae0c0707beb2a9c/typing_extensions-4.15.0-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/b0/7a/620f945b96be1f6ee357d211d5bf74ab1b7fe72a9f1525aafbfe3aee6875/mutagen-1.47.0-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/62/51/72c18c55cf2f46ff4f91ebcc8f75aa30f7305f3d726be3f4ebffb4ae972b/pydantic-2.10.3-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  # YouTube thumbnail dependencies
  resource "yt-dlp" do
    url "https://files.pythonhosted.org/packages/6e/2f/98c3596ad923f8efd32c90dca62e241e8ad9efcebf20831173c357042ba0/yt_dlp-2025.12.8-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "platformdirs" do
    url "https://files.pythonhosted.org/packages/73/cb/ac7874b3e5d58441674fb70742e6c374b28b0c7cb988d37d991cde47166c/platformdirs-4.5.0-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/a7/c2/fe1e52489ae3122415c51f387e221dd0773709bad6c6cdaa599e8a2c5185/urllib3-2.5.0-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/70/7d/9bc192684cea499815ff478dfcdc13835ddf401365057044fb721ec6bddb/certifi-2025.11.12-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/0a/4c/925909008ed5a988ccbb72dcc897407e5d6d3bd72410d69e051fc0c14647/charset_normalizer-3.4.4-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/0e/61/66938bbb5fc52dbdf84594873d5b51fb1f7c7794e9c0f5bd885f30bc507b/idna-3.11-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/1e/db/4254e3eabe8020b458f1a747140d32277ec7a271daf1d235b70dc0b4e6e3/requests-2.32.5-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/a0/e3/59cd50310fc9b59512193629e1984c1f95e5c8ae6e5d8c69532ccc65a7fe/pycparser-2.23-py3-none-any.whl"
    sha256 "1fdc02d174d2dd21456a85a1c3bb40802f6ad9a79dad5e916e30ee2c6a3ad90b"
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

    # Install Japanese man page viewer scripts
    bin.install "jaman"
    bin.install "wrap-ja-man.py"
    bin.install "view-ja-man.sh"

    # Install shell completions
    bash_completion.install "completions/tagger.bash" => "tagger"
    zsh_completion.install "completions/_tagger"
    fish_completion.install "completions/tagger.fish"
  end

  test do
    # Test basic functionality
    system bin/"tagger", "--help"
    system bin/"tagger", "--version"

    # Note: ffmpeg is a runtime dependency (declared in depends_on)
    # It's used for video frame extraction but doesn't need to be tested here

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

    # Test Japanese man page viewer scripts
    assert_predicate bin/"jaman", :exist?, "jaman script should be installed"
    assert_predicate bin/"wrap-ja-man.py", :exist?, "wrap-ja-man.py should be installed"
    assert_predicate bin/"view-ja-man.sh", :exist?, "view-ja-man.sh should be installed"
  end
end
