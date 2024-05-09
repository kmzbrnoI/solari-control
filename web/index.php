<!DOCTYPE html>
<html lang="cz">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow">
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
  <link rel="shortcut icon" href="data:image/x-icon;," type="image/x-icon">
  <title>Nástupištní tabule Solari di Udine</title>
</head>

<?php
setlocale(LC_ALL, 'cs_CZ');

function replaceUTF($text) {
  $toBeReplaced = array('á', 'č', 'š', 'ž', 'Á', 'Č', 'Š', 'Ž');
  $replaceWith = array('az', 'c', 's', 'z', 'Az', 'Cz', 'Sz', 'Zz');
  return str_replace($toBeReplaced, $replaceWith, $text);
}

function compare($a, $b) {
  if (is_int($a["name"]) && is_int($b["name"])) {
    return intval($a["name"]) - intval($b["name"]);
  }

  return strcmp(replaceUTF($a["name"]), replaceUTF($b["name"]));
}

function setOption($inputData, $selected) {
  $value = $inputData["name"];
  $label = $inputData["name"];
  $selectedAttr = "";
  $style = "";

  if (array_key_exists('label', $inputData)) {
    echo htmlentities (print_r ($inputData["label"], true));
    $label = $inputData["label"];
  }

  if (array_key_exists('style', $inputData) && $inputData['style']) {
    $style = "class='".$inputData['style']."'";
  }

  if ($selected) {
    $selectedAttr = 'selected="selected"';
  }

  return '<option value="'.$value.'"'.$selectedAttr.$style.'>'.htmlentities($label).'</option>';
}

$inputJSON = file_get_contents('data.json');
$inputData = json_decode($inputJSON, true);

usort($inputData["types"], "compare");
usort($inputData["direction1"], "compare");
usort($inputData["direction2"], "compare");
usort($inputData["delays"], "compare");

$DEVICE = "/dev/ttyAMA0";

if (isset($_POST["submit"])) {
  $output = null;
  $retval = null;

  if ($_POST["submit"] == "Odeslat do tabule") {
    $dict = [];

    if (isset($_POST['traintype']))
      $dict['type'] = $_POST['traintype'];

    if (isset($_POST['trainnum']))
      $dict['num'] = $_POST['trainnum'];
    if (isset($_POST['trainnum_red']))
      $dict['num_red'] = $_POST['trainnum_red'];

    if (isset($_POST['final']))
      $dict['final'] = $_POST['final'];

    if (isset($_POST['direction1']) && ($_POST['direction1'] != ''))
      $dict['direction1'] = $_POST['direction1'];
    if (isset($_POST['direction2']) && ($_POST['direction2'] != ''))
      $dict['direction2'] = $_POST['direction2'];

    if (isset($_POST['time']) && ($_POST['time'] != '--:--') && ($_POST['time'] != ''))
      $dict['time'] = $_POST['time'];

    if (isset($_POST['delay']))
      $dict['delay'] = $_POST['delay'];

    if (isset($_POST['side']))
      $dict['side'] = 'B';
    else
      $dict['side'] = 'A';

    $encoded = json_encode($dict, JSON_UNESCAPED_UNICODE);

    file_put_contents("content.json", $encoded);
    exec("../sw/control.py set_positions --file=content.json ".$DEVICE." ".$dict['side']." 2>&1", $output, $retval);

  } else if ($_POST["submit"] == "Smazat tabuli") {
    $_POST["traintype"] = "";
    $_POST['trainnum'] = "";
    unset($_POST['trainnum_red']);
    $_POST['final'] = "";
    $_POST['direction1'] = "";
    $_POST['direction2'] = "";
    $_POST['time'] = '--:--';
    $_POST['delay'] = "";

    if (isset($_POST['side']))
      $side = 'B';
    else
      $side = 'A';

    exec("../sw/control.py reset ".$DEVICE." ".$side." 2>&1", $output, $retval);
  }

  if (isset($output)) {
    echo '<script>console.log("Výstup control.py:")</script>';
    echo '<script>console.log("'.implode(",", $output).'")</script>';
  }
}
?>

<body>
  <div class="site-body" id="site-body">
    <div class="text text-header">
      <p>Nástupištní tabule Solari di Udine</p>
    </div>
    <form action="index.php" method="post">
      <div class="text">
        <p>Obsah tabule</p>
      </div>
      <div class="table-main">
        <!-- Table part A -->
        <div class="table-A">
          <!-- Labels row -->
          <div class="label">DRUH VLAKU</div>
          <div class="label">ČÍSLO VLAKU</div>
          <div class="label">CÍLOVÁ STANICE</div>
          <!-- Selectors row -->
          <div>
            <div class="custom-select option-select">
              <select name="traintype">
                <?php
                  foreach($inputData["types"] as $trainType) {
                    if ((isset($_POST["traintype"])) && ($trainType["name"] == $_POST["traintype"])) {
                      echo setOption($trainType, true);
                    } else {
                      echo setOption($trainType, false);
                  }
                  }
                ?>
              </select>
            </div>
          </div>
          <div>
            <input class="option-select option-select-train-num <?php if (isset($_POST['trainnum_red'])) echo "enabledText" ?>"
              id="trainNumInput" type="number" name="trainnum" min="0" max="99999"
              value="<?php if (isset($_POST['trainnum'])) echo $_POST['trainnum']; ?>">
          </div>
          <div>
            <input class="option-select" type="text" name="final" maxlength="14" id="finalDestInput"
            value="<?php if (isset($_POST['final'])) echo $_POST['final']; ?>">
          </div>
        </div>
        <!-- Table part B -->
        <div class="table-B">
          <!-- Labels row -->
          <div class="td-direction-name label">SMĚR</div>
          <div class="label">ODJEZD</div>
          <div class="label">ZPOŽDĚNÍ</div>
          <!-- Selectors row -->
          <div>
            <div class="custom-select option-select">
              <select name="direction1">
                <?php
                foreach($inputData["direction1"] as $dir) {
                    if ((isset($_POST["direction1"])) && ($dir["name"] == $_POST["direction1"])) {
                      echo setOption($dir, true);
                    } else {
                      echo setOption($dir, false);
                    }
                }
                ?>
              </select>
            </div>
          </div>
          <div>
            <div class="custom-select option-select">
              <select name="direction2">
                <?php
                foreach($inputData["direction2"] as $dir) {
                    if ((isset($_POST["direction2"])) &&($dir["name"] == $_POST["direction2"])) {
                      echo setOption($dir, true);
                    } else {
                      echo setOption($dir, false);
                    }
                }
                ?>
              </select>
            </div>
          </div>
          <div></div>
          <div>
            <input type="time" name="time" class="option-select" id="timeInput"
            value="<?php if (isset($_POST['time'])) echo $_POST['time']; ?>">
          </div>
          <div class="option-select-icon">
            <div class="custom-select option-select">
              <select name="delay">
                <?php
                foreach($inputData["delays"] as $delay) {
                    if ((isset($_POST["delay"])) && ($delay["name"] == $_POST["delay"])) {
                      echo setOption($delay, true);
                    } else {
                      echo setOption($delay, false);
                    }
                }
                ?>
              </select>
            </div>
          </div>
        </div>
      </div>
      <!-- Controls -->
      <div class="text">
        <p>Ovládaní tabule</p>
      </div>
      <div class="table-main-control">
        <div class="table-C">
          <div class="table-C-cell">
            <label class="switch">
              <input type="checkbox" name="trainnum_red" onclick="switchText()" <?php if (isset($_POST['trainnum_red'])) echo "checked" ?>>
              <span class="slider"></span>
              <p class="text2"></p>
            </label>
          </div>
          <div class="table-C-cell">
            <label class="switch">
              <input type="checkbox" name="side" <?php if (isset($_POST['side'])) echo "checked" ?>>
              <span class="slider"></span>
              <p class="text2 spec"></p>
            </label>
          </div>
          <div class="table-C-cell">
            <input class="option-select table-C-btn" type="submit" name="submit" value="Odeslat do tabule">
          </div>
          <div class="table-C-cell">
            <input class="option-select table-C-btn" type="submit" name="submit" value="Smazat tabuli">
          </div>
        </div>
      </div>
    </form>
  </div>
</body>

<script>
  let selectDivs = document.getElementsByClassName("custom-select");

  for (let i = 0; i < selectDivs.length; i++) {
    let selectElem = selectDivs[i].getElementsByTagName("select")[0];

    let input = document.createElement("input");
    input.setAttribute("type", "hidden");
    input.setAttribute("name", selectElem.name);
    selectDivs[i].appendChild(input);

    let header = document.createElement("div");
    header.setAttribute("class", "select-header");
    header.innerHTML = selectElem.options[0].innerHTML;
    input.setAttribute("value", selectElem.options[0].value);
    selectDivs[i].appendChild(header);

    let selectBody = document.createElement("div");
    selectBody.setAttribute("class", "select-items select-hide");

    for (let j = 0; j < selectElem.length; j++) {
      let option = document.createElement("div");

      let innerSelectElem = selectElem.options[j].innerHTML.split("?");

      if (innerSelectElem.length > 1) {
        for (let i = 0; i < (innerSelectElem.length - 1); i+=2) {
          if (innerSelectElem[i].includes('fa fa-')) {
            let ico = document.createElement("i");
            ico.setAttribute("class", innerSelectElem[i]);
            ico.classList.add(innerSelectElem[i + 1]);

            option.appendChild(ico);
          } else {
            let span = document.createElement("span");
            span.innerHTML = innerSelectElem[i];
            span.setAttribute("class", innerSelectElem[i + 1]);

            option.appendChild(span);
          }
        }
      } else {
        option.innerHTML = selectElem.options[j].innerHTML;
      }

      option.value = selectElem.options[j].value;

      if (selectElem.options[j].className !== undefined) {
        option.setAttribute("class", selectElem.options[j].className);
      }

      option.addEventListener("click", function(e) {
        let header = this.parentNode.previousSibling;
        header.innerHTML = this.innerHTML;
        input.setAttribute("value", this.value);

        header.setAttribute("class", "select-header");
        if (selectElem.options[j].className !== "") {
          header.classList.add(selectElem.options[j].className);
        }

        header.click();
      });
      selectBody.appendChild(option);

      if (selectElem.options[j].selected) {
        let innerSelectElem = selectElem.options[j].innerHTML.split("?");

        if (innerSelectElem.length > 1) {
          for (let i = 0; i < (innerSelectElem.length - 1); i+=2) {
            if (innerSelectElem[i].includes('fa fa-')) {
            let ico = document.createElement("i");
            ico.setAttribute("class", innerSelectElem[i]);
            ico.classList.add(innerSelectElem[i + 1]);

            header.appendChild(ico);
          } else {
            let span = document.createElement("span");
            span.innerHTML = innerSelectElem[i];
            span.setAttribute("class", innerSelectElem[i + 1]);

            header.appendChild(span);
          }
          }
        } else {
          header.innerHTML = selectElem.options[j].innerHTML;
        }
        input.setAttribute("value", selectElem.options[j].value);

        header.setAttribute("class", "select-header");
        if (selectElem.options[j].className !== "") {
          header.classList.add(selectElem.options[j].className);
        }
      }
    }
    selectDivs[i].appendChild(selectBody);

    header.addEventListener("click", function(e) {
      e.stopPropagation();
      if (this.nextSibling.classList.contains("select-hide")) {
        closeAllSelect();
        this.nextSibling.classList.toggle("select-hide");
        header.classList.toggle("select-header-ico");
      } else {
        closeAllSelect();
      }
    });
  }

  function closeAllSelect() {
    let selectDivs = document.getElementsByClassName("select-items");
    for (i = 0; i < selectDivs.length; i++) {
      selectDivs[i].classList.add("select-hide");
      selectDivs[i].previousSibling.classList.remove("select-header-ico");
    }
  }
  document.addEventListener("click", closeAllSelect);

  function switchText() {
    let elem = document.getElementById("trainNumInput");
    elem.classList.toggle("enabledText");
  }

  let acTrainNum = '';
  function cutTrainNum(event) {
    if (event.target.validity.valid && (parseInt(event.target.value) < 99999 || event.target.value === "") &&
      event.target.value.length < 6) {
      acTrainNum = event.target.value;
    } else {
      event.target.value = acTrainNum;
    }
  }
  document.getElementById("trainNumInput").addEventListener("input", cutTrainNum);

  window.addEventListener("resize", setSizes);
         
  let bodyElem = document.getElementById("site-body");
  let textElems = document.getElementsByClassName("text2");
  function setSizes() {
      let zoom = window.devicePixelRatio;
            
      bodyElem.style.width = 70 * (1500 / screen.width) * zoom + "vw";

      if (zoom < 0) {
        zoom = 0;
      }
      for (let elem of textElems) {
        elem.style.fontSize = (1.15 + 0.25 * Math.log(1 / zoom, 100)) * 100 + "%";
      }
  }
  setSizes();
</script>

</html>
