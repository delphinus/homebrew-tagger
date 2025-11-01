class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.4.0.tar.gz"
  sha256 "ba88c3e70917eb6422ffe700468e4c588b87caf659be2a849ec9f0f67faeaa07"
  license "MIT"

  depends_on "python@3.14"
  depends_on "ffmpeg"

  # Skip relocation of pydantic_core binary (wheel has insufficient header padding)
  skip_clean "libexec"

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/72/94/1a15dd82efb362ac84269196e94cf00f187f7ed21c242792a923cdb1c61f/typing_extensions-4.15.0.tar.gz"
    sha256 "0cea48d173cc12fa28ecabc3b837ea3cf6f38c6d1136f85cbaaf598984861466"
  end

  resource "typing-inspection" do
    url "https://files.pythonhosted.org/packages/55/e3/70399cb7dd41c10ac53367ae42139cf4b1ca5f36bb3dc6c9d33acdb43655/typing_inspection-0.4.2.tar.gz"
    sha256 "ba561c48a67c5958007083d386c3295464928b01faa735ab8547c5692e87f464"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz"
    sha256 "aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89"
  end

  on_arm do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/9e/24/b58a1bc0d834bf1acc4361e61233ee217169a42efbdc15a60296e13ce438/pydantic_core-2.41.4-cp314-cp314-macosx_11_0_arm64.whl"
      sha256 "82df1f432b37d832709fbcc0e24394bba04a01b6ecf1ee87578145c19cde12ac"
    end
  end

  on_intel do
    resource "pydantic-core" do
      url "https://files.pythonhosted.org/packages/54/28/d3325da57d413b9819365546eb9a6e8b7cbd9373d9380efd5f74326143e6/pydantic_core-2.41.4-cp314-cp314-macosx_10_12_x86_64.whl"
      sha256 "e9205d97ed08a82ebb9a307e92914bb30e18cdf6f6b12ca4bedadb1588a0bfe1"
    end
  end

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/81/e6/64bc71b74eef4b68e61eb921dcf72dabd9e4ec4af1e11891bbd312ccbb77/mutagen-1.47.0.tar.gz"
    sha256 "719fadef0a978c31b4cf3c956261b3c58b6948b32023078a2117b1de09f0fc99"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/f3/1e/4f0a3233767010308f2fd6bd0814597e3f63f1dc98304a9112b8759df4ff/pydantic-2.12.3.tar.gz"
    sha256 "1da1c82b0fc140bb0103bc1441ffe062154c8d38491189751ee00fd8ca65ce74"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz"
    sha256 "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e"
  end

  def install
    # Create virtualenv and install resources
    venv = virtualenv_create(libexec, "python3.14")

    # Install non-wheel resources (source tarballs)
    venv.pip_install resources.reject { |r| r.name == "pydantic-core" }

    # Install pydantic-core wheel directly
    pydantic_core_resource = resources.find { |r| r.name == "pydantic-core" }
    venv.pip_install pydantic_core_resource.url

    # Rewrite shebang in tagger script to use virtualenv python
    inreplace "tagger", %r{^#!/usr/bin/env python3$}, "#!#{libexec}/bin/python"

    # Install tagger script
    bin.install "tagger"
  end

  test do
    system bin/"tagger", "--help"
  end
end
