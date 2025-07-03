rm -rf model
mkdir -p model

as_url=https://grlc.io/api-git/hubmapconsortium/ccf-grlc/subdir/mesh-collision/anatomical-structures.csv
patch_url=https://grlc.io/api-git/hubmapconsortium/ccf-grlc/subdir/mesh-collision/placement-patches.csv

curl $as_url -o model/asct-b-grlc.csv
curl $patch_url -o model/reference-organ-grlc.csv