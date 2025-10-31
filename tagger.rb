class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/tagger"
  url "https://github.com/delphinus/tagger/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "" # Update this after creating a GitHub release
  license "MIT"

  depends_on "python@3.14"

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/81/e6/64bc71b74eef4b68e61eb921dcf72dabd9e4ec4af1e11a75a324b96a64bd/mutagen-1.47.0.tar.gz"
    sha256 "719fadef0a978c31b4cf3c956261b3c58b6948b32023078a2117b1de09f0fc99"
  end

  resource "PyYAML" do
    url "https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz"
    sha256 "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"tagger", "--help"
  end
end
