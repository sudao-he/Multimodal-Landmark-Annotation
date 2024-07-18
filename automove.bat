@echo off
md .\raw
md .\raw_align
md .\thermo
md .\thermo_align
md .\thermo_vis
md .\vis
md .\vis_align
set source=.\*_T.JPG
set destination=.\thermo

move %source% %destination%

set source=.\*_W.JPG
set destination=.\vis
move %source% %destination%

set source=.\*_S.JPG
set destination=.\thermo_vis
move %source% %destination%