from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def build_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = int(size * 0.06)
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=(25, 45, 78, 255),
    )

    chart_left = int(size * 0.25)
    chart_bottom = int(size * 0.72)
    bar_width = int(size * 0.095)
    gap = int(size * 0.065)
    heights = (0.20, 0.32, 0.47)
    for index, height in enumerate(heights):
        x0 = chart_left + index * (bar_width + gap)
        y0 = chart_bottom - int(size * height)
        x1 = x0 + bar_width
        y1 = chart_bottom
        draw.rounded_rectangle(
            (x0, y0, x1, y1),
            radius=max(2, int(size * 0.025)),
            fill=(83, 211, 180, 255),
        )

    line_points = [
        (int(size * 0.23), int(size * 0.57)),
        (int(size * 0.39), int(size * 0.48)),
        (int(size * 0.53), int(size * 0.52)),
        (int(size * 0.72), int(size * 0.30)),
    ]
    draw.line(
        line_points,
        fill=(255, 255, 255, 255),
        width=max(4, int(size * 0.035)),
        joint="curve",
    )
    for x, y in line_points:
        r = max(4, int(size * 0.035))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255, 255))

    check = [
        (int(size * 0.57), int(size * 0.74)),
        (int(size * 0.66), int(size * 0.82)),
        (int(size * 0.82), int(size * 0.63)),
    ]
    draw.line(
        check,
        fill=(255, 255, 255, 255),
        width=max(5, int(size * 0.04)),
        joint="curve",
    )
    return image


def main() -> None:
    output_dir = Path(__file__).resolve().parent / "branding"
    output_dir.mkdir(parents=True, exist_ok=True)

    image = build_icon(256)
    png_path = output_dir / "app_icon.png"
    ico_path = output_dir / "app_icon.ico"
    image.save(png_path, format="PNG")
    image.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Created: {png_path}")
    print(f"Created: {ico_path}")


if __name__ == "__main__":
    main()
