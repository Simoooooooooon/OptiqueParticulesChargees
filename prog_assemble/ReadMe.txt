Le but de ce programme est de piloter l'ensemble des alimentations nécessaires au bon fonctionnement du microscope optique. Pour ce faire, on part de deux programmes Python déjà existants :

Le premier est un programme permettant de piloter l'alimentation de la L2. Il s'agissait à la base d'un programme déstiné à deux quadrupoles. Il a donc fallu identifier les parties du code nécessaire pour communiquer avec l'alimentation et modifier ces dernières pour correspondre à une lentille ronde (lentille de Einzel).

Le second est un programme permet de piloter l'alimentation de la source FIB (energie, extracteur, suppresseur et condenseur (L1)). Il a donc fallu comprendre ce programme et le débuguer.

Finalement le but a été de regrouper ces deux programmes, en y ajoutant une interface graphique claire pour contrôler l'ensemble des alimentation du microscope.

=============================================================================================

Notes sur le programme :

- L'interface est réalisée sur QTDesigner ;
- On utilise les librairies PyQt pour faire le lien entre le code et l'interface ;
- La communication série se fait via la librairie serial ;
- On utilise du multi-threading pour imposer et lire des tensions en continu ;

Pour plus d'informations, ce référer directement au programme.
