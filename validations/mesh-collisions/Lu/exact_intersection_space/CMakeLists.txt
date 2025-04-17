cmake_minimum_required(VERSION 3.9)
project(INTERSECTION-SPACE)

# set variables
set(CMAKE_BUILD_TYPE "Release")

# find packages
find_package(CGAL REQUIRED)
set(Boost_USE_STATIC_LIBS OFF) 
set(Boost_USE_MULTITHREADED ON)  
set(Boost_USE_STATIC_RUNTIME OFF) 
find_package(Boost 1.45.0 COMPONENTS filesystem)

add_executable(compute_intersection_space compute_intersection_space.cpp)
target_link_libraries(compute_intersection_space CGAL::CGAL)

if(Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIRS}) 
    target_link_libraries(compute_intersection_space ${Boost_LIBRARIES})
endif()