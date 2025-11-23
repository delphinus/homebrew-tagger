# typed: strict
# frozen_string_literal: true

class Tagger < Formula
  include Language::Python::Virtualenv

  desc "Audio file tag and filename manager using mutagen"
  homepage "https://github.com/delphinus/homebrew-tagger"
  url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/v1.10.3.tar.gz"
  sha256 "de2be1b3a491f391056ccd3ebdda694fcdde23835f8488c31b854540efcfdc48"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "libsndfile"
  depends_on "python@3.12"

  # Optional dependencies for DJ mix segmentation feature
  # Users can install these manually with: pip install librosa numpy

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

    resource "numpy" do
      url "https://files.pythonhosted.org/packages/c5/65/df0db6c097892c9380851ab9e44b52d4f7ba576b833996e0080181c0c439/numpy-2.3.5-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "ee3888d9ff7c14604052b2ca5535a30216aa0a58e948cdd3eeb8d3415f638769"
    end

    resource "scipy" do
      url "https://files.pythonhosted.org/packages/1e/0f/65582071948cfc45d43e9870bf7ca5f0e0684e165d7c9ef4e50d783073eb/scipy-1.16.3-cp312-cp312-macosx_12_0_arm64.whl"
      sha256 "c97176013d404c7346bf57874eaac5187d969293bf40497140b0a2b2b7482e07"
    end

    resource "scikit-learn" do
      url "https://files.pythonhosted.org/packages/43/5d/779320063e88af9c4a7c2cf463ff11c21ac9c8bd730c4a294b0000b666c9/scikit_learn-1.7.2-cp312-cp312-macosx_12_0_arm64.whl"
      sha256 "acbc0f5fd2edd3432a22c69bed78e837c70cf896cd7993d71d51ba6708507476"
    end

    resource "numba" do
      url "https://files.pythonhosted.org/packages/a9/d5/504ce8dc46e0dba2790c77e6b878ee65b60fe3e7d6d0006483ef6fde5a97/numba-0.62.1-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "90fa21b0142bcf08ad8e32a97d25d0b84b1e921bc9423f8dda07d3652860eef6"
    end

    resource "llvmlite" do
      url "https://files.pythonhosted.org/packages/9d/bc/5314005bb2c7ee9f33102c6456c18cc81745d7055155d1218f1624463774/llvmlite-0.45.1-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "1a53f4b74ee9fd30cb3d27d904dadece67a7575198bd80e687ee76474620735f"
    end


    resource "cffi" do
      url "https://files.pythonhosted.org/packages/df/a2/781b623f57358e360d62cdd7a8c681f074a71d445418a776eef0aadb4ab4/cffi-2.0.0-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "8eca2a813c1cb7ad4fb74d368c2ffbbb4789d377ee5bb8df98373c2cc0dee76c"
    end

    resource "soxr" do
      url "https://files.pythonhosted.org/packages/ff/1d/c945fea9d83ea1f2be9d116b3674dbaef26ed090374a77c394b31e3b083b/soxr-1.0.0-cp312-abi3-macosx_11_0_arm64.whl"
      sha256 "e973d487ee46aa8023ca00a139db6e09af053a37a032fe22f9ff0cc2e19c94b4"
    end

    resource "msgpack" do
      url "https://files.pythonhosted.org/packages/34/68/ba4f155f793a74c1483d4bdef136e1023f7bcba557f0db4ef3db3c665cf1/msgpack-1.1.2-cp312-cp312-macosx_11_0_arm64.whl"
      sha256 "446abdd8b94b55c800ac34b102dffd2f6aa0ce643c55dfc017ad89347db3dbdb"
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

    resource "numpy" do
      url "https://files.pythonhosted.org/packages/44/37/e669fe6cbb2b96c62f6bbedc6a81c0f3b7362f6a59230b23caa673a85721/numpy-2.3.5-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "74ae7b798248fe62021dbf3c914245ad45d1a6b0cb4a29ecb4b31d0bfbc4cc3e"
    end

    resource "scipy" do
      url "https://files.pythonhosted.org/packages/40/41/5bf55c3f386b1643812f3a5674edf74b26184378ef0f3e7c7a09a7e2ca7f/scipy-1.16.3-cp312-cp312-macosx_10_14_x86_64.whl"
      sha256 "81fc5827606858cf71446a5e98715ba0e11f0dbc83d71c7409d05486592a45d6"
    end

    resource "scikit-learn" do
      url "https://files.pythonhosted.org/packages/a7/aa/3996e2196075689afb9fce0410ebdb4a09099d7964d061d7213700204409/scikit_learn-1.7.2-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "8d91a97fa2b706943822398ab943cde71858a50245e31bc71dba62aab1d60a96"
    end

    resource "numba" do
      url "https://files.pythonhosted.org/packages/5e/fa/30fa6873e9f821c0ae755915a3ca444e6ff8d6a7b6860b669a3d33377ac7/numba-0.62.1-cp312-cp312-macosx_10_15_x86_64.whl"
      sha256 "1b743b32f8fa5fff22e19c2e906db2f0a340782caf024477b97801b918cf0494"
    end

    resource "llvmlite" do
      url "https://files.pythonhosted.org/packages/e2/7c/82cbd5c656e8991bcc110c69d05913be2229302a92acb96109e166ae31fb/llvmlite-0.45.1-cp312-cp312-macosx_10_15_x86_64.whl"
      sha256 "28e763aba92fe9c72296911e040231d486447c01d4f90027c8e893d89d49b20e"
    end


    resource "cffi" do
      url "https://files.pythonhosted.org/packages/ea/47/4f61023ea636104d4f16ab488e268b93008c3d0bb76893b1b31db1f96802/cffi-2.0.0-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "6d02d6655b0e54f54c4ef0b94eb6be0607b70853c45ce98bd278dc7de718be5d"
    end

    resource "soxr" do
      url "https://files.pythonhosted.org/packages/c5/c7/f92b81f1a151c13afb114f57799b86da9330bec844ea5a0d3fe6a8732678/soxr-1.0.0-cp312-abi3-macosx_10_14_x86_64.whl"
      sha256 "abecf4e39017f3fadb5e051637c272ae5778d838e5c3926a35db36a53e3a607f"
    end

    resource "msgpack" do
      url "https://files.pythonhosted.org/packages/ad/bd/8b0d01c756203fbab65d265859749860682ccd2a59594609aeec3a144efa/msgpack-1.1.2-cp312-cp312-macosx_10_13_x86_64.whl"
      sha256 "70a0dff9d1f8da25179ffcf880e10cf1aad55fdb63cd59c9a49a1b82290062aa"
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

  # DJ mix segmentation dependencies (pure Python packages)
  resource "audioread" do
    url "https://files.pythonhosted.org/packages/7e/16/fbe8e1e185a45042f7cd3a282def5bb8d95bb69ab9e9ef6a5368aa17e426/audioread-3.1.0-py3-none-any.whl"
    sha256 "b30d1df6c5d3de5dcef0fb0e256f6ea17bdcf5f979408df0297d8a408e2971b4"
  end

  resource "decorator" do
    url "https://files.pythonhosted.org/packages/4e/8c/f3147f5c4b73e7550fe5f9352eaa956ae838d5c51eb58e7a25b9f3e2643b/decorator-5.2.1-py3-none-any.whl"
    sha256 "d316bb415a2d9e2d2b3abcc4084c6502fc09240e292cd76a76afc106a1c8e04a"
  end

  resource "joblib" do
    url "https://files.pythonhosted.org/packages/1e/e8/685f47e0d754320684db4425a0967f7d3fa70126bffd76110b7009a0090f/joblib-1.5.2-py3-none-any.whl"
    sha256 "4e1f0bdbb987e6d843c70cf43714cb276623def372df3c22fe5266b2670bc241"
  end

  resource "lazy-loader" do
    url "https://files.pythonhosted.org/packages/83/60/d497a310bde3f01cb805196ac61b7ad6dc5dcf8dce66634dc34364b20b4f/lazy_loader-0.4-py3-none-any.whl"
    sha256 "342aa8e14d543a154047afb4ba8ef17f5563baad3fc610d7b15b213b0f119efc"
  end

  resource "packaging" do
    url "https://files.pythonhosted.org/packages/20/12/38679034af332785aac8774540895e234f4d07f7545804097de4b666afd8/packaging-25.0-py3-none-any.whl"
    sha256 "29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484"
  end

  resource "pooch" do
    url "https://files.pythonhosted.org/packages/a8/87/77cc11c7a9ea9fd05503def69e3d18605852cd0d4b0d3b8f15bbeb3ef1d1/pooch-1.8.2-py3-none-any.whl"
    sha256 "3529a57096f7198778a5ceefd5ac3ef0e4d06a6ddaf9fc2d609b806f25302c47"
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

  resource "threadpoolctl" do
    url "https://files.pythonhosted.org/packages/32/d5/f9a850d79b0851d1d4ef6456097579a9005b31fea68726a4ae5f2d82ddd9/threadpoolctl-3.6.0-py3-none-any.whl"
    sha256 "43a0b8fd5a2928500110039e43a5eed8480b918967083ea48dc3ab9f13c4a7fb"
  end

  resource "pyperclip" do
    url "https://files.pythonhosted.org/packages/30/23/2f0a3efc4d6a32f3b63cdff36cd398d9701d26cda58e3ab97ac79fb5e60d/pyperclip-1.9.0.tar.gz"
    sha256 "b7de0142ddc81bfc5c7507eea19da920b92252b548b96186caf94a5e2527d310"
  end

  resource "soupsieve" do
    url "https://files.pythonhosted.org/packages/d1/c2/fe97d779f3ef3b15f05c94a2f1e3d21732574ed441687474db9d342a7315/soupsieve-2.6-py3-none-any.whl"
    sha256 "e72c4ff06e4fb6e4b5a9f0f55fe6e81514581fca1515028625d0f299c602ccc9"
  end

  resource "beautifulsoup4" do
    url "https://files.pythonhosted.org/packages/6e/74/d53cf0c527b20fc87351e6fd9d51aac9b5d1e32ec5a3a32b84671806ab40/beautifulsoup4-4.13.0-py3-none-any.whl"
    sha256 "9c4c3dfa67aba55f6cd03769c441b21e6a369797fd6766e4b4c6b3399aae2735"
  end

  resource "librosa" do
    url "https://files.pythonhosted.org/packages/b5/ba/c63c5786dfee4c3417094c4b00966e61e4a63efecee22cb7b4c0387dda83/librosa-0.11.0-py3-none-any.whl"
    sha256 "0b6415c4fd68bff4c29288abe67c6d80b587e0e1e2cfb0aad23e4559504a7fa1"
  end

  resource "soundfile" do
    url "https://files.pythonhosted.org/packages/e1/41/9b873a8c055582859b239be17902a85339bec6a30ad162f98c9b0288a2cc/soundfile-0.13.1.tar.gz"
    sha256 "b2c68dab1e30297317080a5b43df57e302584c49e2942defdde0acccc53f0e5b"
  end

  resource "tqdm" do
    url "https://files.pythonhosted.org/packages/d0/30/dc54f88dd4a2b5dc8a0279bdd7270e735851848b762aeb1c1184ed1f6b14/tqdm-4.67.1-py3-none-any.whl"
    sha256 "26445eca388f82e72884e0d580d5464cd801a3ea01e63e5601bdff9ba6a48de2"
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
  end

  test do
    system bin/"tagger", "--help"
  end
end
