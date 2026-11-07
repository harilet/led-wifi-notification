def escape(value):
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Family Alert</title>
<style>
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 24px; background: #0b0b12; color: #f5f5f5; font-family: system-ui, -apple-system, sans-serif; text-align: center; }
h1 { font-size: 1.5rem; margin: 0 0 8px; }
p { color: #aaa; margin: 0 0 24px; }
.buttons { display: grid; gap: 14px; max-width: 420px; width: 100%; margin: 0 auto; }
button { width: 100%; padding: 22px 18px; border: 0; border-radius: 18px; font-size: 1.35rem; font-weight: 600; color: #fff; }
button:active { transform: scale(0.98); }
#msg { min-height: 1.5em; margin-top: 22px; color: #86efac; font-size: 1rem; }
</style>
</head>
<body>
<h1>Family Alert</h1>
<p>Tap a button to alert the desk.</p>
<div class="buttons">__BUTTONS__</div>
<p id="msg"></p>
<script>
async function send(preset) {
  const msg = document.getElementById('msg');
  msg.textContent = 'Sending...';
  try {
    const response = await fetch('/alert', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({preset: preset})
    });
    const result = await response.json();
    if (result.ok) {
      msg.textContent = 'Sent. Waiting for acknowledgement.';
    } else {
      msg.textContent = result.error || 'Could not send.';
    }
  } catch (error) {
    msg.textContent = 'Connection failed.';
  }
}
</script>
</body>
</html>
"""


def render(presets, order=None):
    keys = []
    if order:
        for key in order:
            if key in presets and key not in keys:
                keys.append(key)
    for key in presets:
        if key not in keys:
            keys.append(key)

    buttons = []
    for key in keys:
        preset = presets[key]
        label = preset.get("label", key)
        color = preset.get("color", "#555555")
        if not isinstance(color, str):
            color = "#555555"
        buttons.append(
            '<button data-preset="%s" style="background:%s" '
            'onclick="send(this.dataset.preset)">%s</button>'
            % (escape(key), escape(color), escape(label))
        )
    return PAGE.replace("__BUTTONS__", "".join(buttons))
