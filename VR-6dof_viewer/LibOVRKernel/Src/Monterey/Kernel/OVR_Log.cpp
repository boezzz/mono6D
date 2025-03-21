/************************************************************************************

Filename    :   OVR_Log.cpp
Content     :   Logging support
Created     :   September 19, 2012

Copyright   :   Copyright 2014-2016 Oculus VR, LLC All Rights reserved.

Licensed under the Oculus VR Rift SDK License Version 3.3 (the "License");
you may not use the Oculus VR Rift SDK except in compliance with the License,
which is provided at the time of installation or download, or which
otherwise accompanies this software in either electronic or hard copy form.

You may obtain a copy of the License at

http://www.oculusvr.com/licenses/LICENSE-3.3

Unless required by applicable law or agreed to in writing, the Oculus VR SDK
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

************************************************************************************/

#include "OVR_Log.h"
#include "OVR_Std.h"
#include <stdarg.h>
#include <stdio.h>

#if defined(OVR_OS_WIN32)
#include <windows.h>
#elif defined(OVR_OS_ANDROID)
#include <android/log.h>
#endif

namespace OVR {

// Global Log pointer.
Log* volatile OVR_GlobalLog = 0;

//-----------------------------------------------------------------------------------
// ***** Log Implementation

Log::~Log() {
  // Clear out global log
  if (this == OVR_GlobalLog) {
    // TBD: perhaps we should ASSERT if this happens before system shutdown?
    OVR_GlobalLog = 0;
  }
}

void Log::LogMessageVarg(LogMessageType messageType, const char* fmt, va_list argList) {
  if ((messageType & LoggingMask) == 0)
    return;
#ifndef OVR_BUILD_DEBUG
  if (IsDebugMessage(messageType))
    return;
#endif

  char buffer[MaxLogBufferMessageSize];
  FormatLog(buffer, MaxLogBufferMessageSize, messageType, fmt, argList);
  DefaultLogOutput(messageType, buffer);
}

void OVR::Log::LogMessage(LogMessageType messageType, const char* pfmt, ...) {
  va_list argList;
  va_start(argList, pfmt);
  LogMessageVarg(messageType, pfmt, argList);
  va_end(argList);
}

void Log::FormatLog(
    char* buffer,
    unsigned bufferSize,
    LogMessageType messageType,
    const char* fmt,
    va_list argList) {
  bool addNewline = true;

  switch (messageType) {
    case Log_Error:
      OVR_strcpy(buffer, bufferSize, "Error: ");
      break;
    case Log_Debug:
      OVR_strcpy(buffer, bufferSize, "Debug: ");
      break;
    case Log_Assert:
      OVR_strcpy(buffer, bufferSize, "Assert: ");
      break;
    case Log_Text:
      buffer[0] = 0;
      addNewline = false;
      break;
    case Log_DebugText:
      buffer[0] = 0;
      addNewline = false;
      break;
    default:
      buffer[0] = 0;
      addNewline = false;
      break;
  }

  size_t prefixLength = OVR_strlen(buffer);
  char* buffer2 = buffer + prefixLength;
  OVR_vsprintf(buffer2, bufferSize - prefixLength, fmt, argList);

  if (addNewline)
    OVR_strcat(buffer, bufferSize, "\n");
}

void Log::DefaultLogOutput(LogMessageType messageType, const char* formattedText) {
#if defined(OVR_OS_WIN32)
  // Under Win32, output regular messages to console if it exists; debug window otherwise.
  static DWORD dummyMode;
  static bool hasConsole = (GetStdHandle(STD_OUTPUT_HANDLE) != INVALID_HANDLE_VALUE) &&
      (GetConsoleMode(GetStdHandle(STD_OUTPUT_HANDLE), &dummyMode));

  if (!hasConsole || IsDebugMessage(messageType)) {
    ::OutputDebugStringA(formattedText);
  } else {
    fputs(formattedText, stdout);
  }

#elif defined(OVR_OS_ANDROID)

  int logPriority = ANDROID_LOG_INFO;
  switch (messageType) {
    case Log_DebugText:
    case Log_Debug:
      logPriority = ANDROID_LOG_DEBUG;
      break;
    case Log_Assert:
    case Log_Error:
      logPriority = ANDROID_LOG_ERROR;
      break;
    default:
      logPriority = ANDROID_LOG_INFO;
  }

  __android_log_write(logPriority, "OVR", formattedText);

#else
  fputs(formattedText, stdout);
#endif

  // Just in case.
  OVR_UNUSED2(formattedText, messageType);
}

// static
void Log::SetGlobalLog(Log* log) {
  OVR_GlobalLog = log;
}
// static
Log* Log::GetGlobalLog() {
  // No global log by default?
  //    if (!OVR_GlobalLog)
  //        OVR_GlobalLog = GetDefaultLog();
  return OVR_GlobalLog;
}

// static
Log* Log::GetDefaultLog() {
  // Create default log pointer statically so that it can be used
  // even during startup.
  static Log defaultLog;
  return &defaultLog;
}

//-----------------------------------------------------------------------------------
// ***** Global Logging functions

// The log functions are defined in both debug and release builds so that that debug applications
// can link against release builds of the libovrkernel library and still output debugging info.
// In the case where both the application and the library are release builds, this will
// have no adverse effect as long as LogDebugText, LogDebug and LogAssert are always
// called via the OVR_DEBUG_LOG, OVR_DEBUG_LOG_TEXT and OVR_ASSERT_LOG macros because
// the macros define OVR_ASSERT_LOG, etc. away in release.
inline void LogFn(LogMessageType msgType, const char* fmt, va_list args) {
  if (OVR_GlobalLog) {
    OVR_GlobalLog->LogMessageVarg(msgType, fmt, args);
  }
}

void LogText(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  LogFn(Log_Text, fmt, args);
  va_end(args);
}

void LogError(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  LogFn(Log_Error, fmt, args);
  va_end(args);
}

void LogDebug(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  LogFn(Log_Debug, fmt, args);
  va_end(args);
}

void LogDebugText(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  LogFn(Log_DebugText, fmt, args);
  va_end(args);
}

void LogAssert(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  LogFn(Log_Assert, fmt, args);
  va_end(args);
}

} // namespace OVR
