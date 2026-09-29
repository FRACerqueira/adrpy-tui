# adrpy config does not accept a folder leading outside the repository

The fidelity pass reported that `adrpy config --folderlog ../x` is accepted. Re-run by the main model: `..`, `../outside/log` and `doc/../../..` are refused (path-outside-repository); `doc/../log` is accepted. The real path is a hand-edited config file, which adrpy reads back unchecked (see configured-folder-outside-the-repository).
