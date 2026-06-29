import AppKit
import Foundation

let outDir = URL(fileURLWithPath: CommandLine.arguments[1])
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

let W: CGFloat = 848
let H: CGFloat = 384
let fps = 30
let seconds = 34
let totalFrames = fps * seconds

func c(_ hex: UInt32, _ a: CGFloat = 1) -> NSColor {
    NSColor(calibratedRed: CGFloat((hex >> 16) & 255) / 255,
            green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255,
            alpha: a)
}

func lerp(_ a: CGFloat, _ b: CGFloat, _ t: CGFloat) -> CGFloat { a + (b - a) * t }
func clamp(_ v: CGFloat, _ lo: CGFloat = 0, _ hi: CGFloat = 1) -> CGFloat { min(max(v, lo), hi) }
func smooth(_ t: CGFloat) -> CGFloat { let x = clamp(t); return x * x * (3 - 2 * x) }

func text(_ s: String, x: CGFloat, y: CGFloat, size: CGFloat, color: NSColor = .white, weight: NSFont.Weight = .regular, align: NSTextAlignment = .left, width: CGFloat = 500) {
    let p = NSMutableParagraphStyle()
    p.alignment = align
    let attrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: size, weight: weight),
        .foregroundColor: color,
        .paragraphStyle: p
    ]
    (s as NSString).draw(in: NSRect(x: x, y: H - y - size - 8, width: width, height: size + 14), withAttributes: attrs)
}

func textBlock(_ s: String, x: CGFloat, y: CGFloat, size: CGFloat, height: CGFloat, color: NSColor = .white, weight: NSFont.Weight = .regular, align: NSTextAlignment = .left, width: CGFloat = 500) {
    let p = NSMutableParagraphStyle()
    p.alignment = align
    p.lineSpacing = 4
    let attrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: size, weight: weight),
        .foregroundColor: color,
        .paragraphStyle: p
    ]
    (s as NSString).draw(in: NSRect(x: x, y: H - y - height, width: width, height: height), withAttributes: attrs)
}

func rect(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, _ color: NSColor, r: CGFloat = 10) {
    color.setFill()
    NSBezierPath(roundedRect: NSRect(x: x, y: H - y - h, width: w, height: h), xRadius: r, yRadius: r).fill()
}

func line(_ a: CGPoint, _ b: CGPoint, _ color: NSColor, _ width: CGFloat = 1.5) {
    color.setStroke()
    let p = NSBezierPath()
    p.lineWidth = width
    p.move(to: a)
    p.line(to: b)
    p.stroke()
}

func dot(_ p: CGPoint, _ radius: CGFloat, _ color: NSColor) {
    color.setFill()
    NSBezierPath(ovalIn: NSRect(x: p.x - radius, y: H - p.y - radius, width: radius * 2, height: radius * 2)).fill()
}

func arrow(_ from: CGPoint, _ to: CGPoint, _ label: String, _ progress: CGFloat, _ color: NSColor) {
    let q = CGPoint(x: lerp(from.x, to.x, progress), y: lerp(from.y, to.y, progress))
    line(CGPoint(x: from.x, y: H - from.y), CGPoint(x: q.x, y: H - q.y), color, 2)
    dot(CGPoint(x: q.x, y: q.y), 4, color)
    if progress > 0.72 {
        text(label, x: to.x + 10, y: to.y - 8, size: 15, color: color, weight: .semibold, width: 170)
    }
}

func background(_ time: CGFloat) {
    let grad = NSGradient(colors: [c(0x050608), c(0x091014), c(0x11100d)])!
    grad.draw(in: NSRect(x: 0, y: 0, width: W, height: H), angle: 18)
    c(0xffffff, 0.04).setStroke()
    for x in stride(from: CGFloat(0), through: W, by: 48) { line(CGPoint(x: x, y: 0), CGPoint(x: x + 60, y: H), c(0xffffff, 0.03), 1) }
    for y in stride(from: CGFloat(30), through: H, by: 42) { line(CGPoint(x: 0, y: y), CGPoint(x: W, y: y), c(0xffffff, 0.025), 1) }
    let pulse = 0.5 + 0.5 * sin(time * 1.7)
    dot(CGPoint(x: 720, y: 76), 95 + pulse * 18, c(0xd8b26a, 0.06))
    dot(CGPoint(x: 138, y: 288), 82, c(0x69d2c6, 0.045))
}

func drawToken(_ s: String, _ x: CGFloat, _ y: CGFloat, _ active: Bool = false) {
    rect(x, y, 112, 34, active ? c(0xd8b26a, 0.22) : c(0xffffff, 0.08), r: 8)
    c(active ? 0xd8b26a : 0xffffff, active ? 0.8 : 0.18).setStroke()
    let p = NSBezierPath(roundedRect: NSRect(x: x, y: H - y - 34, width: 112, height: 34), xRadius: 8, yRadius: 8)
    p.lineWidth = 1
    p.stroke()
    text(s, x: x, y: y + 8, size: 14, color: active ? c(0xffe2a3) : c(0xd8dde0), weight: .semibold, align: .center, width: 112)
}

func title(_ main: String, _ sub: String) {
    text("EVIDENTIA", x: 34, y: 28, size: 17, color: c(0xd8b26a), weight: .bold, width: 220)
    text(main, x: 34, y: 58, size: 30, color: c(0xf7f2e8), weight: .bold, width: 560)
    text(sub, x: 36, y: 96, size: 16, color: c(0xaeb8bd), width: 650)
}

func sceneTokens(_ t: CGFloat) {
    title("Dental knowledge becomes tokens", "A clinical case is split into recoverable meaning units.")
    let words = ["Ceramic", "CIELAB", "Value", "Chroma", "Texture", "Layering"]
    for (i, w) in words.enumerated() {
        let delay = CGFloat(i) * 0.12
        let a = smooth((t - delay) / 0.35)
        drawToken(w, 84 + CGFloat(i % 3) * 136, 166 + CGFloat(i / 3) * 52, a > 0.65)
    }
    rect(526, 148, 238, 148, c(0xffffff, 0.06), r: 16)
    text("Case input", x: 552, y: 170, size: 16, color: c(0xd8b26a), weight: .semibold)
    textBlock("Photos\nshade tabs\ntechnician notes\nprotocol PDFs", x: 552, y: 198, size: 16, height: 92, color: c(0xe7ecef), width: 190)
}

func sceneEmbedding(_ t: CGFloat) {
    title("Embeddings encode ceramic meaning", "Each token becomes a direction in clinical-technical space.")
    let origin = CGPoint(x: 180, y: 272)
    let targets: [(String, CGPoint, NSColor)] = [
        ("Ceramic", CGPoint(x: 386, y: 130), c(0xd8b26a)),
        ("CIELAB", CGPoint(x: 456, y: 236), c(0x69d2c6)),
        ("Value", CGPoint(x: 332, y: 300), c(0xf2f2f0)),
        ("Chroma", CGPoint(x: 576, y: 170), c(0xff8f70)),
        ("Translucency", CGPoint(x: 616, y: 292), c(0x9bd0ff))
    ]
    rect(92, 106, 620, 238, c(0xffffff, 0.045), r: 18)
    dot(origin, 6, c(0xffffff))
    for (i, item) in targets.enumerated() {
        let p = smooth((t - CGFloat(i) * 0.11) / 0.48)
        arrow(origin, item.1, item.0, p, item.2)
    }
    text("embedding vector", x: 96, y: 284, size: 15, color: c(0xaeb8bd))
}

func sceneMap(_ t: CGFloat) {
    title("Vector map of dental expertise", "Similar evidence clusters together: color, mass, texture, substrate and outcome.")
    let clusters: [(String, CGPoint, NSColor)] = [
        ("Shade", CGPoint(x: 230, y: 164), c(0xd8b26a)),
        ("Masses", CGPoint(x: 448, y: 136), c(0x69d2c6)),
        ("Texture", CGPoint(x: 588, y: 238), c(0xff8f70)),
        ("Substrate", CGPoint(x: 314, y: 286), c(0x9bd0ff)),
        ("Outcome", CGPoint(x: 658, y: 116), c(0xd6a7ff))
    ]
    for a in clusters {
        for b in clusters {
            if a.0 < b.0 {
                let d = hypot(a.1.x - b.1.x, a.1.y - b.1.y)
                if d < 330 { line(CGPoint(x: a.1.x, y: H - a.1.y), CGPoint(x: b.1.x, y: H - b.1.y), c(0xffffff, 0.08), 1) }
            }
        }
    }
    for (i, cl) in clusters.enumerated() {
        let grow = smooth((t - CGFloat(i) * 0.12) / 0.45)
        for j in 0..<13 {
            let ang = CGFloat(j) * 0.83 + CGFloat(i)
            let r = CGFloat(18 + (j % 5) * 7) * grow
            let p = CGPoint(x: cl.1.x + cos(ang) * r, y: cl.1.y + sin(ang) * r)
            dot(p, 2.5 + grow * 1.2, cl.2.withAlphaComponent(0.55))
        }
        dot(cl.1, 8 + grow * 2, cl.2)
        text(cl.0, x: cl.1.x - 46, y: cl.1.y + 20, size: 15, color: cl.2, weight: .semibold, align: .center, width: 92)
    }
}

func sceneMLP(_ t: CGFloat) {
    title("Reasoning layer", "Patterns activate: shade drift, ceramic recipe and evidence source.")
    let xs: [CGFloat] = [130, 300, 470, 640]
    let labels = ["Input\nEvidence", "Embedding\nSpace", "Dental\nRules", "RAG\nAnswer"]
    for i in 0..<4 {
        rect(xs[i], 142, 118, 102, c(0xffffff, 0.07), r: 14)
        textBlock(labels[i], x: xs[i], y: 168, size: 17, height: 62, color: i == 3 ? c(0xd8b26a) : c(0xe7ecef), weight: .semibold, align: .center, width: 118)
        if i < 3 {
            let p = smooth((t - CGFloat(i) * 0.18) / 0.45)
            arrow(CGPoint(x: xs[i] + 118, y: 193), CGPoint(x: xs[i+1] - 8, y: 193), "", p, c(0x69d2c6))
        }
    }
    rect(214, 270, 420, 34, c(0xd8b26a, 0.12), r: 12)
    text("ceramic signal -> evidence-backed answer", x: 0, y: 280, size: 16, color: c(0xffe2a3), weight: .semibold, align: .center, width: W)
}

func sceneAnswer(_ t: CGFloat) {
    title("Dental Knowledge Map", "A private vector mirror that turns scattered clinical evidence into defensible decisions.")
    rect(80, 142, 688, 160, c(0xffffff, 0.07), r: 18)
    text("Query", x: 112, y: 166, size: 15, color: c(0xd8b26a), weight: .bold)
    text("Why does this crown lose value in the incisal third?", x: 112, y: 194, size: 23, color: c(0xf7f2e8), weight: .semibold, width: 610)
    let lines = [
        "3 sources retrieved: polarized photo, CIELAB note, firing protocol",
        "Likely cause: value drop + excessive grey translucency",
        "Next action: adjust incisal mass and verify under calibrated light"
    ]
    for (i, l) in lines.enumerated() {
        let a = smooth((t - CGFloat(i) * 0.22) / 0.45)
        if a > 0.02 {
            dot(CGPoint(x: 126, y: 238 + CGFloat(i) * 26), 4, c(0x69d2c6, a))
            text(l, x: 144, y: 228 + CGFloat(i) * 26, size: 16, color: c(0xdce7e8, a), width: 580)
        }
    }
}

for frame in 0..<totalFrames {
    autoreleasepool {
        let time = CGFloat(frame) / CGFloat(fps)
        let image = NSImage(size: NSSize(width: W, height: H))
        image.lockFocus()
        background(time)
        let scene = Int(time / 6.8)
        let local = (time - CGFloat(scene) * 6.8) / 6.8
        switch scene {
        case 0: sceneTokens(local)
        case 1: sceneEmbedding(local)
        case 2: sceneMap(local)
        case 3: sceneMLP(local)
        default: sceneAnswer(local)
        }
        image.unlockFocus()
        let rep = NSBitmapImageRep(data: image.tiffRepresentation!)!
        let png = rep.representation(using: .png, properties: [:])!
        let name = String(format: "frame_%04d.png", frame)
        try! png.write(to: outDir.appendingPathComponent(name))
    }
    if frame % 100 == 0 { print("frame \(frame)/\(totalFrames)") }
}
