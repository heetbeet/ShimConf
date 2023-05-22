#ifndef SHIM_CONF_UTIL_HPP
#define SHIM_CONF_UTIL_HPP
#pragma comment(lib, "shell32.lib")

#include <windows.h>
#include <string>
#include <iostream>
#include <filesystem>
#include <lua.hpp>
#include <vector>
#include <string>
#include <shellapi.h>
#include <unicode/unistr.h>

std::string convertWstringToUtf8(const std::wstring& wstr)
{
    icu::UnicodeString unicode_str(reinterpret_cast<const UChar*>(wstr.c_str()));
    std::string utf8_str;
    unicode_str.toUTF8String(utf8_str);
    return utf8_str;
}

std::wstring convertUtf8ToWstring(const std::string& utf8_str)
{
    icu::UnicodeString unicode_str = icu::UnicodeString::fromUTF8(utf8_str);
    std::wstring wstr(reinterpret_cast<const wchar_t*>(unicode_str.getBuffer()), unicode_str.length());
    return wstr;
}

std::tuple<std::filesystem::path, std::vector<std::wstring>> get_path_and_cmd_args_vec() {
    int argc = 0;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    std::vector<std::wstring> cmdArgsVec;

    std::filesystem::path path(argv[0]);

    if(argv != nullptr) {
        for(int i = 1; i < argc; ++i) {
            cmdArgsVec.push_back(argv[i]);
        }

        // The array returned by CommandLineToArgvW should be deallocated using LocalFree
        LocalFree(argv);
    }
    return std::make_tuple(path, cmdArgsVec);
}

std::wstring get_cmd_args_string() {
    std::wstring cmdArgsString(GetCommandLineW());

    bool inQuote = false;
    size_t i;
    for (i = 0; i < cmdArgsString.size(); ++i) {
        if (cmdArgsString[i] == L'"') { inQuote = !inQuote; }
        if (cmdArgsString[i] == L' ' && !inQuote) { break; }
    }

    while (i < cmdArgsString.size() && cmdArgsString[i] == L' ') { ++i; }

    cmdArgsString = cmdArgsString.substr(i);
    return cmdArgsString;
}


std::tuple<std::wstring, std::wstring, std::wstring, std::wstring, std::wstring, std::vector<std::wstring>> get_cmd_info() {
    auto [path, cmdArgsVec] = get_path_and_cmd_args_vec();
    std::wstring path_to_this_exe = path.wstring();
    std::wstring path_to_this_dir = path.parent_path().wstring();
    std::wstring filename = path.filename().wstring();
    std::wstring filename_noext = path.stem().filename().wstring();
    std::wstring cmdArgsString = get_cmd_args_string();

    return std::make_tuple(path_to_this_exe, path_to_this_dir, filename, filename_noext, cmdArgsString, cmdArgsVec);
}


int execute(const std::wstring& exec, const std::wstring& arguments, bool shell, bool wait_for_exit) {
    if (shell) {
        std::wcout << L"Calling '" << exec << L" " << arguments << L"'\n";
    }

    int exit_code = 0;
    std::wstring cmd = exec + L" " + arguments;

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi;

    BOOL success = CreateProcessW(
        NULL,
        cmd.data(),
        NULL,
        NULL,
        TRUE,
        shell ? NULL : CREATE_NO_WINDOW,
        NULL,
        NULL,
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
        if (shell) {
            std::wcout << L"ShimConf failed: " << GetLastError() << L'\n';
        }
        return -1;
    }

    return exit_code;
}

void run_lua_and_execute() {
    // Get the command info
    auto [shimFilePath, shimDirPath, shimFileName, shimFileNameNoExt, shimArgsString, shimArgsVec] = get_cmd_info();

    // Find the Lua script
    std::filesystem::path luaScriptPath = shimDirPath + L"\\" + shimFileNameNoExt + L".lua";

    // Check if Lua script file exists
    if(!std::filesystem::exists(luaScriptPath)) {
        std::wcerr << L"Lua script not found: " << luaScriptPath.wstring() << '\n';
        return;
    }

    // Initialize Lua
    lua_State* L = luaL_newstate();
    luaL_openlibs(L);

    // Convert wstring to UTF-8 string
    std::string shimFilePathStr = convertWstringToUtf8(shimFilePath);
    std::string shimDirPathStr = convertWstringToUtf8(shimDirPath);
    std::string shimFileNameStr = convertWstringToUtf8(shimFileName);
    std::string shimFileNameNoExtStr = convertWstringToUtf8(shimFileNameNoExt);
    std::string shimArgsStringStr = convertWstringToUtf8(shimArgsString);

    // Set variables in the Lua state
    lua_pushstring(L, shimFilePathStr.c_str());
    lua_setglobal(L, "shimFilePath");
    lua_pushstring(L, shimDirPathStr.c_str());
    lua_setglobal(L, "shimDirPath");
    lua_pushstring(L, shimFileNameStr.c_str());
    lua_setglobal(L, "shimFileName");
    lua_pushstring(L, shimFileNameNoExtStr.c_str());
    lua_setglobal(L, "shimFileNameNoExt");
    lua_pushstring(L, shimArgsStringStr.c_str());
    lua_setglobal(L, "shimArgsString");

    // Run the Lua script
    if(luaL_dofile(L, luaScriptPath.string().c_str()) != LUA_OK) {
        std::cerr << "Failed to run Lua script: " << lua_tostring(L, -1) << '\n';
        lua_close(L);
        return;
    }

    // Get the `exec` and `args` variables from Lua
    lua_getglobal(L, "exec");
    lua_getglobal(L, "args");
    if(!lua_isstring(L, -2) || !lua_isstring(L, -1)) {
        std::cerr << "Lua script did not set `exec` and `args` variables correctly.\n";
        lua_close(L);
        return;
    }

    // Convert Lua strings to C++ strings
    std::string exec(lua_tostring(L, -2));
    std::string args(lua_tostring(L, -1));

    // Convert UTF-8 string to wstring
    std::wstring execWstr = convertUtf8ToWstring(exec);
    std::wstring argsWstr = convertUtf8ToWstring(args);

    // Run the `execute` function
    //int result = execute(execWstr, argsWstr, true, true);

    // Close Lua

    std::wcout << L"exec: " << execWstr << L'\n';
    std::wcout << L"args: " << argsWstr << L'\n';
    
    lua_close(L);
}


#endif // SHIM_CONF_UTIL_HPP
