with import <nixpkgs> {};

python3.pkgs.buildPythonPackage {
  name = "int3";
  src = ./.;
  propagatedBuildInputs = [
    (python3Packages.buildPythonPackage rec {
      name = "clang-${version}";
      version = "6.0.0.2";
      buildInputs = [ clang_6 ];
      src = fetchFromGitHub {
        owner = "ethanhs";
        repo = "clang";
        rev = version;
        sha256 = "1qqc5m5qqyc5qrp4mmxkkjx2d91dkdh49kgl2817cdanvmv1hq9q";
      };

      postPatch = ''
        substituteInPlace clang/cindex.py \
          --replace "'libclang.so'" "'${llvmPackages_6.clang-unwrapped.lib}/lib/libclang.so'" 
      '';
    })
  ];
}
