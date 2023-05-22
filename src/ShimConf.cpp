#include <shimconfutil.hpp>

#ifdef SHELL
    int wmain() {

        run_lua_and_execute();
        auto [path_to_this_exe, path_to_this_dir, filename, filename_noext, cmdArgsString, cmdArgsVec] = get_cmd_info();
        
        std::wcout  << L"path_to_this_exe: " << path_to_this_exe << std::endl;
        std::wcout  << L"path_to_this_dir: " << path_to_this_dir << std::endl;
        std::wcout  << L"filename: " << filename << std::endl;
        std::wcout  << L"filename_noext: " << filename_noext << std::endl;
        std::wcout << L"cmdArgsString: " << cmdArgsString << std::endl;
        std::wcout  << L"cmdArgsVec: ";
        for (auto& arg : cmdArgsVec) {
            std::wcout << arg << L" ";
        }
        std::wcout << std::endl;

        return execute(L"notepad.exe", L"", true, true);
    }
#else
    int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
        return execute(L"notepad.exe", L"", false, true);
    }
#endif