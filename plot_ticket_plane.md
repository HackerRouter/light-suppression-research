nonspawn_shift_compact

python plot_ticket_plane.py --range=59,57:69,67 --player-ticket=64,62,3,PLAYER --highlight=60,64:62,66 --annotate --output ../output/nonspawn_shift_compact_ticket_plane.png


nonspawn_shift

python plot_ticket_plane.py --range=59,59:69,69 --player-ticket=64,64,3,PLAYER --highlight=60,62:62,68 --annotate --output ../output/nonspawn_shift_ticket_plane.png


orig_relog

orig_nonspawn

python plot_ticket_plane.py --range=56,60:66,70 --player-ticket=61,65,3,PLAYER --highlight=60,62:62,68 --annotate --output ../output/nonspawn_ticket_plane.png

orig_spawn
python plot_ticket_plane.py --range=-12,-12:12,12 --start-ticket=0,0,START --highlight=-2,-2:0,4 --annotate --output ../output/spawn_ticket_plane.png

orig_portal

python plot_ticket_plane.py --range=58,62:64,68 --portal-ticket=61,65,PORTAL --highlight=60,62:62,68 --annotate --output ../output/orig_portal_ticket_plane.png

portal
python plot_ticket_plane.py --range=58,62:64,68 --portal-ticket=61,65,PORTAL --highlight=60,64:62,66 --annotate --output ../output/portal_ticket_plane.png


portal_shift
python plot_ticket_plane.py --range=59,62:65,68 --portal-ticket=62,65,PORTAL --highlight=60,64:62,66 --annotate --output ../output/portal_shift_ticket_plane.png

portal_shift_2
python plot_ticket_plane.py --range=59,61:65,67 --portal-ticket=62,64,PORTAL --highlight=60,64:62,66 --annotate --output ../output/portal_shift_2_ticket_plane.png

1side

python plot_ticket_plane.py --range=-12,-12:12,12 --start-ticket=0,0,START --highlight=0,-2:0,10 --annotate --output ../output/1side_ticket_plane.png

2side

python plot_ticket_plane.py --range=-12,-12:12,12 --start-ticket=0,0,START --highlight=0,-6:0,6 --annotate --output ../output/2side_ticket_plane.png