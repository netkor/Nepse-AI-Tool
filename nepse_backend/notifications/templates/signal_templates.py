# Simple helpers to render signal-based notifications

def render_signal_telegram(signal_history):
    # signal_history is expected to be a SignalHistory or dict with keys: signal_type, direction, price, strength, message
    s = signal_history
    lines = [f"<b>Signal</b>: {s.get('signal_type')}", f"Direction: {s.get('direction')}", f"Price: {s.get('price')}", f"Strength: {s.get('strength'):.2f}"]
    if s.get('message'):
        lines.append(f"Note: {s.get('message')}")
    return "\n".join(lines)


def render_signal_email(signal_history):
    s = signal_history
    subject = f"{s.get('signal_type')} signal: {s.get('direction')} @ {s.get('price')}"
    body = f"Signal: {s.get('signal_type')}\nDirection: {s.get('direction')}\nPrice: {s.get('price')}\nStrength: {s.get('strength'):.2f}\n"
    if s.get('message'):
        body += f"\n{ s.get('message') }\n"
    return subject, body
