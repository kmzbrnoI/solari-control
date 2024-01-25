<!DOCTYPE html>
<html lang="cz">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow">
  <link rel="stylesheet" href="style.css">
  <title>Nástupištní tabule Solari di Udine</title>
</head>

<?php
setlocale(LC_ALL, 'cs_CZ');

$TRAINTYPES = array('Ec', 'Ic', 'Ex R', 'Ex lůžkový', 'Ex', 'R R', 'R lůžkový',
'R', 'Sp', 'Os', 'Mim. Ex', 'Mim. R', 'Mim. Sp', 'Mim. Os', 'Zvláštní vlak',
'Special train', 'Parní vlak', 'Steam train', 'IR', 'ICE', 'Sc', 'TGV', 'Ic
bílá');
sort($TRAINTYPES, SORT_LOCALE_STRING);

$DIR1 = array(
    'Adamov', 'Adamov-Blansko', 'Bylnice', 'Blansko', 'Blažovice', 'Bohumín',
    'Břeclav', 'Břeclav-Kúty', 'Břeclav-Bratislava', 'Bučovice', 'Bzenec',
    'Česká Třebová', 'Č.Třebová-Pardubice', 'Havlíčkův Brod', 'Holubice',
    'Horní Cerekev', 'Hradec Králové', 'Jihlava', 'Jihlava-Horní Cerekev',
    'Kolín', 'Kojetín', 'Kroměříž', 'Křižanov', 'Kunovice', 'Kuřim', 'Kuřim-Tišnov',
    'Kyjov', 'Modřice', 'Moravské Bránice', 'Moravský Krumlov', 'Náměšť nad Oslavou',
    'Nezamyslice', 'Olomouc hl.n.', 'Olomouc-Uničov', 'Ostrava hl.n.',
    'Ostrava-Vítkovice', 'Pardubice hl.n.', 'Praha-Holešovice', 'Přerov',
    'Přerov-Bohumín', 'Prostějov hl.n.', 'Prostějov-Olomouc', 'Rajhrad',
    'Rousínov', 'Šakvice', 'Skalice nad Svitavou', 'Sokolnice-Teln.', 'Střelice',
    'Studenec', 'Studénka', 'Tišnov', 'Veselí nad Moravou', 'Vranovice',
    'Vyškov na Moravě', 'Zastávka u Brna', 'Žďár nad Sázavou',
    'Štúrovo', 'Svitavy', 'Tábor', 'Tišnov-Křižanov', 'Trenč. Teplá',
    'Turnov', 'Uherské Hradiště', ''
);
sort($DIR1, SORT_LOCALE_STRING);

$DIR2 = array(
    'Blansko', 'Bohumín', 'Bojkovice', 'Břeclav', 'Bratislava', 'Bylnice',
    'Bučovice', 'Bzenec', 'Čadca', 'České Budějovice', 'Český Těšín', 'Chornice',
    'Děčin', 'Frýdek-Místek', 'Havířov', 'Havlíčkův Brod', 'Holubice', 'Horní Cerekev',
    'Hradec Králové', 'Hranice na Moravě', 'Hrušovany nad Jevišovkou', 'Hulín',
    'Kolína', 'Komárno', 'Kyjov', 'Kyjov Bzenec', 'Křižanov', 'Kunovice', 'Kúty',
    'Moravské Bránice', 'Moravský Krumlov', 'Moravský Písek', 'Moravská Třebová',
    'Mosty u Jablunkova', 'Náměšť nad Oslavou', 'Nezamyslice', 'Nové Město na Moravě',
    'Okříšky', 'Ostrava hl.n.', 'Ostrava-Svinov', 'Ostrava-Vítkovice', 'Pardubice hl.n.',
    'Pardubice-Kolín', 'Praha-Holešovice', 'Přerov', 'S1', 'S2', 'S3', 'S4', 'S41',
    'S5', 'S6', 'S7', 'R1', 'R2', 'R3', 'R4', 'R41', 'R5', 'R6', 'R7', 'Uničov',
    'Ústí nad Labem', 'Valašské Meziřící', 'Veselí nad Lužnicí', 'Veseá nad Moravou',
    'Vyškov na Moravě', 'Zábřeh na Moravě', 'Zaječí', 'Žďár nad Sázavou', 'Žilina',
    'Kojetín', 'Vlárský Průsmyk', 'Tábor-Veselí nad Lužnicí', 'Praha hl.n.',
    'ODKLON', ''
);
sort($DIR2, SORT_LOCALE_STRING);

$DELAYS = array(
    0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100, 110,
    120, 130, 140, 150, 160, 170, 180, 200, 220, 240, 260, 280, 300, 330, 360,
    390, 420, 450, 480, '>480', 'VLAK NEJEDE', 'BUS'
);

$SIDES = array('A', 'B');

$DEVICE = "/dev/ttyAMA0";

if (isset($_POST["submit"])) {
  $output = null;
  $retval = null;

  if ($_POST["submit"] == "Odeslat do tabule") {
    $dict = [
      "num" => $_POST["trainnum"],
      "type" => $_POST["traintype"],
      "final" => $_POST["final"],
      "delay" => $_POST["delay"],
    ];
    if (isset($_POST['trainnum_red']))
      $dict['num_red'] = $_POST['trainnum_red'];
    if (isset($_POST['direction1']) && ($_POST['direction1'] != ''))
      $dict['direction1'] = $_POST['direction1'];
    if (isset($_POST['direction2']) && ($_POST['direction2'] != ''))
      $dict['direction2'] = $_POST['direction2'];
    if (isset($_POST['time']) && ($_POST['time'] != '--:--') && ($_POST['time'] != ''))
      $dict['time'] = $_POST['time'];

    //print_r($dict);

    $encoded = json_encode($dict, JSON_UNESCAPED_UNICODE);
    file_put_contents("content.json", $encoded);
    exec("../sw/control.py set_positions --file=content.json ".$DEVICE." ".$_POST["side"]." 2>&1", $output, $retval);

  } else if ($_POST["submit"] == "Smazat tabuli") {
    exec("../sw/control.py reset ".$DEVICE." ".$_POST["side"]." 2>&1", $output, $retval);
  }
}
?>

<body>
  <h1>Nástupištní tabule Solari di Udine</h1>
  <hr>
  <form action="index.php" method="post">
    <label for="trainnum">Číslo vlaku:</label> <br>
    <input type="number" name="trainnum" max="99999" value="<?php if (isset($_POST['trainnum'])) echo $_POST['trainnum']; ?>">

    <input type="checkbox" name="trainnum_red" <?php if (isset($_POST['trainnum_red']) && $_POST['trainnum_red']) { echo 'checked'; } ?>>
    <label for="trainnum_red">Zobrazit číslo vlaku červeně</label><br>

    <label for="traintype">Typ vlaku:</label><br>
    <select name="traintype">
    <?php
    foreach($TRAINTYPES as $type) {
        if ((isset($_POST["traintype"])) && ($type == $_POST["traintype"])) {
            echo '<option selected="selected">'.$type.'</option>';
        } else {
            echo '<option>'.$type.'</option>';
        }
    }
    ?>
    </select> <br>


    <label for="final">Cílová stanice (max 14 znaků):</label> <br>
    <input type="text" name="final" maxlength="14" value="<?php if (isset($_POST['final'])) echo $_POST['final']; ?>"> <br>

    <label for="time">Čas odjezdu:</label> <br>
    <input type="time" name="time" value="<?php if (isset($_POST['time'])) echo $_POST['time']; ?>"> <br>

    <label for="direction1">Směr 1:</label> <br>
    <select name="direction1">
    <?php
    foreach($DIR1 as $dir) {
        if ((isset($_POST["direction1"])) && ($dir == $_POST["direction1"])) {
            echo '<option selected="selected">'.$dir.'</option>';
        } else {
            echo '<option>'.$dir.'</option>';
        }
    }
    ?>
    </select> <br>

    <label for="direction2">Směr 2:</label> <br>
    <select name="direction2" value="">
    <?php
    foreach($DIR2 as $dir) {
        if ((isset($_POST["direction2"])) &&($dir == $_POST["direction2"])) {
            echo '<option selected="selected">'.$dir.'</option>';
        } else {
            echo '<option>'.$dir.'</option>';
        }
    }
    ?>
    </select> <br>

    <label for="delay">Zpoždění (minut):</label><br>
    <select name="delay">
    <?php
    foreach($DELAYS as $delay) {
        if ((isset($_POST["delay"])) && ($delay == $_POST["delay"])) {
            echo '<option value="'.$delay.'" selected="selected">'.$delay.'</option>';
        } else {
            echo '<option value="'.$delay.'">'.$delay.'</option>';
        }
    }
    ?>
    </select> <br>

    <label for="side">Strana:</label><br>
    <select name="side">
      <option value="A" selected="selected">Přední</option>
      <option value="B">Zadní</option>
    </select> <br>

    <br>
    <input type="submit" name="submit" value="Odeslat do tabule">
    <input type="submit" name="submit" value="Smazat tabuli"> <br>
  </form>

  <?php
  if (isset($output)) {
    echo '<br><hr>';
    echo 'Výstup control.py:<br>';
    echo '<pre>';
    echo(implode("\n", $output));
    echo '</pre>';
  }
  ?>

</body>
</html>
