#
# Copyright (c) 2016-2017 Vinnie Falco (vinnie dot falco at gmail dot com)
#
# Distributed under the Boost2x Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# Official repository: https://github.com/boostorg/beast
#

cmake_minimum_required(VERSION 3.10 FATAL_ERROR)
project(CppCon2018 VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(Boost_USE_STATIC_LIBS ON)

if(MSVC)
  set (Boost_USE_STATIC_RUNTIME ON)
  add_definitions(-D_WIN32_WINNT=0x0601)
  add_definitions(-D_SCL_SECURE_NO_WARNINGS=1)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS=1)
  add_definitions(-D_SILENCE_CXX17_ALLOCATOR_VOID_DEPRECATION_WARNING)
  add_compile_options(/MP)
  string(REPLACE "/W3" "/W4" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
else()
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
endif()

set_property(GLOBAL PROPERTY USE_FOLDERS ON)
set_property(GLOBAL PROPERTY PREDEFINED_TARGETS_FOLDER build)

# this ultimately depended on an ubuntu install
# possibly don't need some of this anymore...
set(OPENSSL_USE_STATIC_LIBS TRUE)
set(OPENSSL_ROOT_DIR /usr/local/ssl/lib)
set(OPENSSL_INCLUDE_DIR /usr/local/ssl/include/openssl)
find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIRS})
link_directories(${OPENSSL_LIBRARY_DIRS})
message(STATUS "Using OpenSSL ${OPENSSL_VERSION}")


find_package(ZLIB)

# needed the boost_root hint
set(BOOST_ROOT /home/harlan/ucsb/projects/exos_internship/CryptoStrat_Internship/connector/cpp/include/boost_1_73_0)
find_package(Boost REQUIRED COMPONENTS system)
include_directories(${Boost_INCLUDE_DIRS})
link_directories(${Boost_LIBRARY_DIRS})

file(GLOB_RECURSE BEAST_FILES
  ${Boost_INCLUDE_DIRS}/boost/beast/*.hpp
  ${Boost_INCLUDE_DIRS}/boost/beast/*.ipp)

source_group(TREE ${Boost_INCLUDE_DIRS}/boost/beast PREFIX beast FILES ${BEAST_FILES})

# # we use a third party (non boost) json library; it's a single header file we stick in the project tree itself...
# # similar to root_certificates.hpp
file(GLOB APP_FILES
  beast.hpp
  nlohmann/json.hpp
  ore.hpp
  main.cpp
  net.hpp)

source_group("" FILES ${APP_FILES})

add_executable(websocket-msg-client-sync ${APP_FILES} ${BEAST_FILES})

if(NOT WIN32)
  find_package(Threads)
  target_link_libraries(websocket-msg-client-sync PRIVATE Threads::Threads ${Boost_SYSTEM_LIBRARY} OpenSSL::SSL OpenSSL::Crypto ZLIB::ZLIB dl)
  target_include_directories(websocket-msg-client-sync PRIVATE msgpack-c/include)
endif()

set_target_properties(websocket-msg-client-sync PROPERTIES
  VS_DEBUGGER_WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY
  VS_STARTUP_PROJECT websocket-msg-client-sync)
