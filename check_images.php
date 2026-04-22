<?php

$dir = '20260422';
$csv_file = $dir . '/deployments_20260422.csv';

$handle = fopen($csv_file, 'r');
$header = fgetcsv($handle, escape: '');
$col = array_flip($header);
$rows = [];
while (($row = fgetcsv($handle, escape: '')) !== false) {
  $rows[] = $row;
}
fclose($handle);

function gdrive_img_url(string $url): string
{
  if (preg_match('/[?&]id=([\w-]+)/', $url, $m)) {
    return 'https://lh3.googleusercontent.com/d/' . $m[1];
  }
  return $url;
}

?>
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <title>Check Images</title>
  <style>
    body {
      font-family: sans-serif;
      font-size: 14px;
    }

    table {
      border-collapse: collapse;
    }

    th,
    td {
      border: 1px solid #ccc;
      padding: 6px 10px;
      text-align: left;
      vertical-align: middle;
    }

    th {
      background: #eee;
    }

    img {
      max-height: 160px;
      max-width: 200px;
      cursor: crosshair;
      display: block;
    }

    #magnifier {
      display: none;
      position: fixed;
      z-index: 999;
      pointer-events: none;
      width: 220px;
      height: 220px;
      border: 2px solid #555;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
      background-repeat: no-repeat;
      background-color: #fff;
    }
  </style>
</head>

<body>
  <h2>Deployments: <?= htmlspecialchars($dir) ?></h2>
  <table>
    <tr>
      <th>dataset</th>
      <th>locationID</th>
      <th>deviceID</th>
      <th>deviceImage</th>
    </tr>
    <?php foreach ($rows as $row): ?>
      <tr>
        <td><?= htmlspecialchars($row[$col['dataset']]) ?></td>
        <td><?= htmlspecialchars($row[$col['locationID']]) ?></td>
        <td><?= htmlspecialchars($row[$col['deviceID']]) ?></td>
        <td style="white-space:nowrap">
          <img src="<?= htmlspecialchars(gdrive_img_url($row[$col['deviceImage']])) ?>" alt="device image" style="vertical-align:middle">
          <a href="<?= htmlspecialchars($row[$col['deviceImage']]) ?>" target="_blank" style="margin-left:8px;font-size:12px;vertical-align:middle">full image</a>
        </td>
      </tr>
    <?php endforeach; ?>
  </table>

  <div id="magnifier"></div>

  <script>
    const mag = document.getElementById('magnifier');
    const LENS = 220; // lens square size in px
    const ZOOM = 3; // magnification factor
    const OFFSET = 16;

    document.querySelectorAll('td img').forEach(img => {
      img.addEventListener('mouseenter', () => {
        mag.style.backgroundImage = `url('${img.src}')`;
        mag.style.display = 'block';
      });

      img.addEventListener('mousemove', e => {
        const rect = img.getBoundingClientRect();

        // mouse position relative to the rendered thumbnail
        const rx = e.clientX - rect.left;
        const ry = e.clientY - rect.top;

        // scale factor from natural image size to rendered size
        const scaleX = img.naturalWidth / rect.width;
        const scaleY = img.naturalHeight / rect.height;

        // background size: full image zoomed by ZOOM, scaled to rendered size
        const bgW = img.naturalWidth / scaleX * ZOOM;
        const bgH = img.naturalHeight / scaleY * ZOOM;

        // offset so the hovered point sits at the centre of the lens
        const bgX = -(rx * ZOOM - LENS / 2);
        const bgY = -(ry * ZOOM - LENS / 2);

        mag.style.backgroundSize = `${bgW}px ${bgH}px`;
        mag.style.backgroundPosition = `${bgX}px ${bgY}px`;

        // position lens next to cursor, stay inside viewport
        let x = e.clientX + OFFSET;
        let y = e.clientY + OFFSET;
        if (x + LENS > window.innerWidth) x = e.clientX - LENS - OFFSET;
        if (y + LENS > window.innerHeight) y = e.clientY - LENS - OFFSET;
        mag.style.left = x + 'px';
        mag.style.top = y + 'px';
      });

      img.addEventListener('mouseleave', () => {
        mag.style.display = 'none';
      });
    });
  </script>
</body>

</html>