class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.4.0.tar.gz"
  sha256 "ba88c3e70917eb6422ffe700468e4c588b87caf659be2a849ec9f0f67faeaa07"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/81/e6/64bc71b74eef4b68e61eb921dcf72dabd9e4ec4af1e11891bbd312ccbb77/mutagen-1.47.0.tar.gz"
    sha256 "719fadef0a978c31b4cf3c956261b3c58b6948b32023078a2117b1de09f0fc99"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/45/0f/27908242621b14e649a84e62b133de45f84c255eecb350ab02979844a788/pydantic-2.10.3.tar.gz"
    sha256 "cb5ac360ce894ceacd69c403187900a02c4b20b693a9dd1d643e1effab9eadf9"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz"
    sha256 "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e"
  end

  def install
    # Create virtualenv and install resources
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install resources

    # Rewrite shebang in tagger script to use virtualenv python
    inreplace "tagger", %r{^#!/usr/bin/env python3$}, "#!#{libexec}/bin/python"

    # Install tagger script
    bin.install "tagger"
  end

  test do
    system bin/"tagger", "--help"
  end
end
