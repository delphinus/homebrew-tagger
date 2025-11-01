class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.4.0.tar.gz"
  sha256 "ba88c3e70917eb6422ffe700468e4c588b87caf659be2a849ec9f0f67faeaa07"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"tagger", "--help"
  end
end
