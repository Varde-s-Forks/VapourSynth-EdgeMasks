project('EdgeMasks', 'cpp',
  default_options: ['buildtype=release', 'warning_level=2', 'b_lto=true', 'b_ndebug=if-release', 'cpp_std=c++17'],
  license: 'MIT',
  meson_version: '>=0.51.0',
  version: '3.1',
)

cxx = meson.get_compiler('cpp')

# True when the compiler understands GCC/clang-style arguments (gcc/clang)
gcc_syntax = cxx.get_argument_syntax() == 'gcc'

# Detect compiler id to choose proper flags for clang vs gcc vs msvc
compiler_id = cxx.get_id()
is_clang = compiler_id == 'clang' or compiler_id == 'apple-clang'

if get_option('buildtype') == 'release'
  add_project_arguments(gcc_syntax ? ['-fno-math-errno', '-fno-trapping-math'] : '/GS-', language: 'cpp')
endif

sources = files('EdgeMasks/edgemasks.cpp')

if gcc_syntax
  vapoursynth_dep = dependency('vapoursynth', version: '>=55').partial_dependency(compile_args: true, includes: true)
  install_dir = vapoursynth_dep.get_variable(pkgconfig: 'libdir') / 'vapoursynth'
else
  vapoursynth_dep = []
  install_dir = get_option('libdir') / 'vapoursynth'
endif

libs = []

# Prepare SIMD-specific argument lists for different compilers/toolchains.
# We will test if the compiler accepts AVX-512 flags and only build AVX-512 then.
sse4_cpp_args = []
avx2_cpp_args = []
avx512_cpp_args = []
build_avx512 = false

if gcc_syntax
  if is_clang
    # clang / apple-clang: use -msse4.1 and -mavx2 (add -mfma recommended)
    sse4_cpp_args = ['-msse4.1']
    avx2_cpp_args = ['-mavx2', '-mfma']  # -mfma recommended by vectorclass when using avx2

    # Candidate AVX-512 flags the code needs; test them individually and gather the supported subset.
    avx512_candidates = ['-mavx512f', '-mavx512bw', '-mavx512dq', '-mavx512vl']
    foreach a : avx512_candidates
      if cxx.has_argument(a)
        avx512_cpp_args += [a]
      endif
    endforeach

    # If we got at least the core AVX-512 feature, enable building the avx512 lib.
    # Prefer requiring avx512f and avx512bw (pack ops need bw), but be lenient and
    # enable when at least avx512f + avx512bw/dq present.
    if avx512_cpp_args.contains('-mavx512f') and (avx512_cpp_args.contains('-mavx512bw') or avx512_cpp_args.contains('-mavx512dq'))
      build_avx512 = true
    else
      message('AVX-512 flags not fully supported by compiler; skipping avx512 target. Detected flags: ' + avx512_cpp_args.to_string())
      avx512_cpp_args = []  # ensure empty if unsupported
    endif

  else
    # GCC-style toolchains: use -march variants (as original) + -mfma for avx2
    sse4_cpp_args = ['-march=x86-64-v2']
    avx2_cpp_args = ['-march=x86-64-v3', '-mfma']
    # GCC supports -march for fine-grained tuning; -march=x86-64-v4 was used previously for avx512
    # But we'll also test explicit AVX-512 flags for safety
    if cxx.has_argument('-mavx512f')
      # collect a set of avx512 flags if available
      avx512_candidates = ['-mavx512f', '-mavx512bw', '-mavx512dq', '-mavx512vl']
      foreach a : avx512_candidates
        if cxx.has_argument(a)
          avx512_cpp_args += [a]
        endif
      endforeach
      if avx512_cpp_args.contains('-mavx512f') and (avx512_cpp_args.contains('-mavx512bw') or avx512_cpp_args.contains('-mavx512dq'))
        build_avx512 = true
      else
        message('AVX-512 flags not fully supported by compiler; skipping avx512 target. Detected flags: ' + avx512_cpp_args.to_string())
        avx512_cpp_args = []
      endif
    else
      # If no -mavx512f support, skip avx512
      build_avx512 = false
    endif
  endif
else
  # For MSVC (non-gcc_syntax) keep your previous style
  sse4_cpp_args = ['/arch:SSE2']
  avx2_cpp_args = ['/arch:AVX2']
  avx512_cpp_args = ['/arch:AVX512']  # MSVC-style; you may still want to test support
  # For MSVC you can assume build_avx512 true only if you are confident the toolchain supports it.
  build_avx512 = true
endif

if host_machine.cpu_family().startswith('x86')
  add_project_arguments('-DEDGEMASKS_X86', language: 'cpp')

  libs += static_library('instrset_detect',
    files('EdgeMasks/vectorclass/instrset_detect.cpp'),
    gnu_symbol_visibility: 'hidden',
  )

  libs += static_library('sse4',
    files('EdgeMasks/edgemasks_sse4.cpp'),
    cpp_args: sse4_cpp_args,
    dependencies: vapoursynth_dep,
    gnu_symbol_visibility: 'hidden',
  )

  libs += static_library('avx2',
    files('EdgeMasks/edgemasks_avx2.cpp'),
    cpp_args: avx2_cpp_args,
    dependencies: vapoursynth_dep,
    gnu_symbol_visibility: 'hidden',
  )

  # Only add the avx512 static library if the compiler actually supports needed flags.
  if build_avx512
    libs += static_library('avx512',
      files('EdgeMasks/edgemasks_avx512.cpp'),
      cpp_args: avx512_cpp_args,
      dependencies: vapoursynth_dep,
      gnu_symbol_visibility: 'hidden',
    )
  else
    message('Not building avx512 target because compiler AVX-512 support was not detected.')
  endif
endif

shared_module('edgemasks',
  sources,
  dependencies: vapoursynth_dep,
  gnu_symbol_visibility: 'hidden',
  install: true,
  install_dir: install_dir,
  link_with: libs,
  name_prefix: '',
)
