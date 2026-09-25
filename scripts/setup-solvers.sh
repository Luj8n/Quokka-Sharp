#!/usr/bin/env bash
# Install GPMC, Ganak, and d4 maxT locally, without messing with the system itself.
# Files installed by this script stay within this repository.
# GPMC and maxT use local libraries plus the OS's standard C library
# (glibc on Linux); they are not fully static.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
local_dir="$root/.solvers"
bin_dir="$local_dir/bin"
env_dir="$local_dir/env"
src_dir="$local_dir/src"

case "$(uname -s):$(uname -m)" in
  Linux:x86_64)
    platform=linux-64; ganak_platform=linux-amd64
    mamba_sha=366cd9cd8be14df1ab8ed50352a82111082a36686b2d389fdb79a92c3fafb3e3
    ganak_sha=ac84b42eb83a23ce8b09f2468ea59468ec4948321d9696216c6528603a33eb63 ;;
  Linux:aarch64|Linux:arm64)
    platform=linux-aarch64; ganak_platform=linux-arm64
    mamba_sha=9f93b974adcb4d166996af969b6cd371287d1a3e52733704727884d9b74cb7a7
    ganak_sha=8a01f915792d22e41631dc6e94396f71d7d372f1b44fc51eacca970666ccfb38 ;;
  Darwin:x86_64)
    platform=osx-64; ganak_platform=mac-x86_64
    mamba_sha=1e71054bb3ac9a076e21f7ec48acfef536f9b3f1408f371a942784bf5ef83d8a
    ganak_sha=ccced5273894fe28cd3c145d427b2161d790a1373faf351df8824ba498874428 ;;
  Darwin:arm64)
    platform=osx-arm64; ganak_platform=mac-arm64
    mamba_sha=ec2a072f028e1a7cf20f3e2e74d5a8127cf5a5f27636375b5359811565f4e5be
    ganak_sha=b527c061cc101744dd1b0e641aee2cde2c2a606556cfd3b8c0e31c495bd6bc46 ;;
  *) echo "Unsupported platform: $(uname -s) $(uname -m)" >&2; exit 1 ;;
esac

gpmc_rev=df1aea7769887b62f59b803293678a1bbc5fe06d
d4_rev=c121982c16b8195a617567e41ba3b63742d1edb1
ganak_version=v2.7.0

main() {
  check_bootstrap_tools
  prepare_install
  trap cleanup EXIT
  install_toolchain
  build_gpmc
  build_d4
  install_ganak
  echo "Installed GPMC, Ganak, and maxT in $bin_dir"
}

check_bootstrap_tools() {
  local tool
  for tool in curl tar; do
    command -v "$tool" >/dev/null || { echo "Required bootstrap tool missing: $tool" >&2; return 1; }
  done
}

prepare_install() {
  if [[ -e "$local_dir" ]]; then
    echo "Solver directory already exists: $local_dir (remove it to reinstall)" >&2
    return 1
  fi
  mkdir -p "$bin_dir" "$src_dir" "$local_dir/cache" "$local_dir/tmp"
  export XDG_CACHE_HOME="$local_dir/cache" TMPDIR="$local_dir/tmp"
}

install_toolchain() {
  echo "Downloading local build environment for $platform"
  download_verified "https://github.com/mamba-org/micromamba-releases/releases/download/2.9.0-0/micromamba-$platform" "$bin_dir/micromamba" "$mamba_sha"
  chmod +x "$bin_dir/micromamba"
  export MAMBA_ROOT_PREFIX="$local_dir/mamba" CONDA_PKGS_DIRS="$local_dir/mamba/pkgs"
  local extra_packages=() candidate
  if [[ "$platform" == osx-* ]]; then extra_packages+=("binutils_impl_$platform"); fi
  "$bin_dir/micromamba" create -y -p "$env_dir" -c conda-forge --override-channels \
    'cmake>=4.1' make \
    cxx-compiler gmp mpfr zlib boost-cpp "${extra_packages[@]}"
  for candidate in "$env_dir/bin/"*-conda-linux-gnu-ar "$env_dir/bin/"*-apple-darwin*-ar; do
    if [[ -x "$candidate" ]]; then ln -sf "$candidate" "$env_dir/bin/ar"; break; fi
  done
  [[ -L "$env_dir/bin/ar" ]] || { echo "Local GNU ar was not installed" >&2; return 1; }
}

download_verified() {
  curl -fsSL --retry 3 "$1" -o "$2"
  check_sha "$2" "$3"
}

check_sha() {
  local actual
  if command -v sha256sum >/dev/null; then
    actual=$(sha256sum "$1"); actual=${actual%% *}
  else
    actual=$(shasum -a 256 "$1"); actual=${actual%% *}
  fi
  [[ "$actual" == "$2" ]] || { echo "Checksum mismatch: $1" >&2; exit 1; }
}

build_gpmc() {
  echo "Building GPMC"
  local gpmc_src="$src_dir/gpmc"
  extract "https://codeload.github.com/System-Verification-Lab/GPMC/tar.gz/$gpmc_rev" "$gpmc_src"
  run cmake -S "$gpmc_src" -B "$gpmc_src/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  run cmake --build "$gpmc_src/build" --parallel 2
  install -m 755 "$gpmc_src/build/gpmc" "$bin_dir/gpmc"
}

extract() {
  mkdir -p "$2"
  curl -fsSL --retry 3 "$1" | tar -xz -C "$2" --strip-components=1
}

run() { "$bin_dir/micromamba" run -p "$env_dir" "$@"; }

build_d4() {
  echo "Building d4 Max#SAT solver"
  local d4_src="$src_dir/d4"
  extract "https://codeload.github.com/jm62300/d4/tar.gz/$d4_rev" "$d4_src"
  # Upstream uses unbounded make -j; cap its builds at two jobs.
  sed -i.bak 's/make -j/make -j2/g' "$d4_src/build.sh" "$d4_src/3rdParty/bipe/build.sh"
  rm "$d4_src/build.sh.bak" "$d4_src/3rdParty/bipe/build.sh.bak"
  (cd "$d4_src" && run bash ./build.sh)
  run make -C "$d4_src/demo/maxT" -j2 "LIBS=-L$env_dir/lib -Wl,-rpath,$env_dir/lib ../../build/libd4.a -lboost_program_options -lz -lgmpxx -lgmp"
  install -m 755 "$d4_src/demo/maxT/build/maxT" "$bin_dir/maxT"
  ln -s maxT "$bin_dir/maxT_static"
}

install_ganak() {
  echo "Installing Ganak"
  local archive="$local_dir/ganak.tar.gz"
  download_verified "https://github.com/meelgroup/ganak/releases/download/release/$ganak_version/ganak-$ganak_version-$ganak_platform.tar.gz" "$archive" "$ganak_sha"
  tar -xzf "$archive" -C "$bin_dir" ganak
  chmod +x "$bin_dir/ganak"
}

cleanup() {
  local status=$?
  if (( status == 0 )); then
    rm -f "$local_dir/ganak.tar.gz"
  else
    echo "Setup failed; removing the incomplete .solvers directory" >&2
    rm -rf "$local_dir"
  fi
}

main
