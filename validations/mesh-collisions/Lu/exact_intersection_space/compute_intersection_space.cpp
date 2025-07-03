#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Surface_mesh.h>
#include <CGAL/Polygon_mesh_processing/corefinement.h>
#include <CGAL/Polygon_mesh_processing/IO/polygon_mesh_io.h>
#include <fstream>

typedef CGAL::Exact_predicates_inexact_constructions_kernel   K;
typedef CGAL::Surface_mesh<K::Point_3>                        Mesh;
namespace PMP = CGAL::Polygon_mesh_processing;


int main(int argc, char* argv[])
{
    const std::string filename1 = (argc > 1) ? argv[1] : CGAL::data_file_path("meshes/blobby.off");
    const std::string filename2 = (argc > 2) ? argv[2] : CGAL::data_file_path("meshes/eight.off");
    const std::string out_filename = (argc > 3) ? argv[3] : "intersection.off";
    
    Mesh mesh1, mesh2;
    if(!PMP::IO::read_polygon_mesh(filename1, mesh1) || !PMP::IO::read_polygon_mesh(filename2, mesh2))
    {
        std::cerr << "Invalid input." << std::endl;
        return 1;
    }
    
    Mesh out;
    bool valid_intersection = PMP::corefine_and_compute_intersection(mesh1,mesh2, out);
    if(valid_intersection)
    {
        std::cout << "Intersection was successfully computed\n";
        CGAL::IO::write_polygon_mesh(out_filename, out, CGAL::parameters::stream_precision(17));
        return 0;
    }
    std::cout << "Intersection could not be computed\n";
    return 1;
}