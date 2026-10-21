"""Wrapping and a bounded, scrollable detail panel for map diagnostics."""
import pygame


def wrapped_lines(font, text, width):
    lines = []
    for paragraph in text.splitlines() or [""]:
        line = ""
        for char in paragraph:
            if line and font.size(line+char)[0] > width:
                lines.append(line)
                line = ""
            line += char
        lines.append(line)
    return lines


def draw_text_panel(screen, font, title, text, scroll):
    rect = screen.get_rect().inflate(-60, -80)
    pygame.draw.rect(screen, (19, 26, 40), rect, border_radius=9)
    pygame.draw.rect(screen, (235, 135, 110), rect, 2, border_radius=9)
    heading = font.render(title, True, (245, 205, 185))
    screen.blit(heading, (rect.x+16, rect.y+12))
    lines = wrapped_lines(font, text, rect.width-32)
    capacity = max(1, (rect.height-68)//font.get_linesize())
    scroll = max(0, min(scroll, len(lines)-capacity))
    for index, line in enumerate(lines[scroll:scroll+capacity]):
        screen.blit(font.render(line, True, (235, 240, 250)),
                    (rect.x+16, rect.y+48+index*font.get_linesize()))
    return scroll
