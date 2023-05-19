#include <windows.h>
#include <string>
#include <iostream>

namespace shim {
    class CommandExecutor {
    public:
        static int execute(const std::wstring& process, const std::wstring& arguments, const std::wstring& working_directory, bool is_gui, bool wait_for_exit, bool requires_elevation) {
            std::wcout << L"Calling '" << process << L" " << arguments << L"'\n";

            int exit_code = 0;

            // Construct the command
            std::wstring cmd = process + L" " + arguments;

            STARTUPINFOW si = { sizeof(si) };
            PROCESS_INFORMATION pi;

            BOOL success = CreateProcessW(
                NULL,
                cmd.data(),
                NULL,
                NULL,
                TRUE,
                is_gui ? NULL : CREATE_NO_WINDOW,
                NULL,
                working_directory.c_str(),
                &si,
                &pi
            );

            if (success) {
                if (wait_for_exit) {
                    WaitForSingleObject(pi.hProcess, INFINITE);
                    DWORD dwExitCode;
                    GetExitCodeProcess(pi.hProcess, &dwExitCode);
                    exit_code = static_cast<int>(dwExitCode);
                    CloseHandle(pi.hProcess);
                    CloseHandle(pi.hThread);
                }
            } else {
                std::wcout << L"CreateProcess failed: " << GetLastError() << L'\n';
            }

            return exit_code;
        }
    };
}

int wmain() {
    return shim::CommandExecutor::execute(L"cmd.exe", L"/k echo hello", L"c:\\", false, true, false);
}
