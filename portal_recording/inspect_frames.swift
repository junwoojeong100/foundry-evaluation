import Foundation
import Vision
import ImageIO

struct Finding: Codable {
    let kind: String
    let box: [Double]
}

struct FrameResult: Codable {
    let file: String
    let findings: [Finding]
    let bodyTextLines: Int
}

let args = CommandLine.arguments
guard args.count == 3 else {
    fatalError("Usage: inspect_frames.swift <frame-directory> <result.json>")
}
let directory = URL(fileURLWithPath: args[1], isDirectory: true)
let files = try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension == "png" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
let expressions = try [
    ("personal", NSRegularExpression(pattern: "junwoo|/(Users|home)/", options: [.caseInsensitive])),
    ("email", NSRegularExpression(pattern: "[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}")),
    ("credential", NSRegularExpression(pattern: "(InstrumentationKey|AccountKey|SharedAccessKey)=|[?&](sig|access_token)=", options: [.caseInsensitive]))
]
var results: [FrameResult] = []
for file in files {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US", "ko-KR"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(url: file).perform([request])
    var findings: [Finding] = []
    var bodyLines = 0
    for observation in request.results ?? [] {
        guard let text = observation.topCandidates(1).first?.string else { continue }
        let box = observation.boundingBox
        if box.minY > 0.13 && box.maxY < 0.92 { bodyLines += 1 }
        for (kind, expression) in expressions {
            if expression.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) != nil {
                findings.append(Finding(kind: kind, box: [box.minX, box.minY, box.width, box.height]))
            }
        }
    }
    results.append(FrameResult(file: file.lastPathComponent, findings: findings, bodyTextLines: bodyLines))
}
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
try encoder.encode(results).write(to: URL(fileURLWithPath: args[2]))
print("Offline OCR inspected \(results.count) frames; findings: \(results.reduce(0) { $0 + $1.findings.count })")
