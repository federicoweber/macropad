import AVFoundation
import CoreGraphics
import CoreMedia
import Foundation
import ScreenCaptureKit

private let spotifyBundleIdentifier = "com.spotify.client"

final class AudioMeter: NSObject, SCStreamOutput, SCStreamDelegate, @unchecked Sendable {
    private var lowPassState: Float = 0
    private var midPassState: Float = 0
    private var smoothedBands = [Float](repeating: 0, count: 3)
    private var lastOutputTime = CFAbsoluteTimeGetCurrent()

    func stream(
        _ stream: SCStream,
        didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
        of outputType: SCStreamOutputType
    ) {
        guard outputType == .audio, sampleBuffer.isValid else { return }

        try? sampleBuffer.withAudioBufferList { audioBufferList, _ in
            guard
                let description = sampleBuffer.formatDescription?.audioStreamBasicDescription,
                let format = AVAudioFormat(
                    standardFormatWithSampleRate: description.mSampleRate,
                    channels: description.mChannelsPerFrame
                ),
                let samples = AVAudioPCMBuffer(
                    pcmFormat: format,
                    bufferListNoCopy: audioBufferList.unsafePointer
                ),
                let channels = samples.floatChannelData
            else { return }

            let frameCount = Int(samples.frameLength)
            let channelCount = Int(samples.format.channelCount)
            guard frameCount > 0, channelCount > 0 else { return }

            let sampleRate = description.mSampleRate
            let lowCoefficient = Float(1 - exp(-2 * Double.pi * 240 / sampleRate))
            let midCoefficient = Float(1 - exp(-2 * Double.pi * 2_400 / sampleRate))
            var bandSquares = [Float](repeating: 0, count: 3)

            for frame in 0..<frameCount {
                var sample: Float = 0
                for channel in 0..<channelCount {
                    sample += channels[channel][frame]
                }
                sample /= Float(channelCount)

                lowPassState += lowCoefficient * (sample - lowPassState)
                midPassState += midCoefficient * (sample - midPassState)
                let bands = [
                    lowPassState,
                    midPassState - lowPassState,
                    sample - midPassState,
                ]
                for band in 0..<3 {
                    bandSquares[band] += bands[band] * bands[band]
                }
            }

            let gains: [Float] = [1.5, 1.2, 2.0]
            for band in 0..<3 {
                let rms = sqrt(bandSquares[band] / Float(frameCount)) * gains[band]
                let decibels = 20 * log10(max(rms, 0.000_001))
                let normalized = min(1, max(0, (decibels + 55) / 43))
                let smoothing: Float = normalized > smoothedBands[band] ? 0.7 : 0.22
                smoothedBands[band] += (normalized - smoothedBands[band]) * smoothing
            }

            let now = CFAbsoluteTimeGetCurrent()
            if now - lastOutputTime >= (1.0 / 30.0) {
                print(String(
                    format: "%.3f,%.3f,%.3f",
                    smoothedBands[0],
                    smoothedBands[1],
                    smoothedBands[2]
                ))
                fflush(stdout)
                lastOutputTime = now
            }
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        fputs("Spotify audio capture stopped: \(error)\n", stderr)
        exit(1)
    }
}

@main
struct SpotifyAudioMeter {
    static func main() async {
        do {
            let permissionGranted = (
                CGPreflightScreenCaptureAccess() || CGRequestScreenCaptureAccess()
            )
            if !permissionGranted {
                fputs(
                    "Screen & System Audio Recording permission is required\n",
                    stderr
                )
                exit(4)
            }
            if CommandLine.arguments.contains("--request-permission") {
                return
            }
            let content = try await SCShareableContent.excludingDesktopWindows(
                false,
                onScreenWindowsOnly: false
            )
            guard let spotify = content.applications.first(where: {
                $0.bundleIdentifier == spotifyBundleIdentifier
            }) else {
                fputs("Spotify is not running\n", stderr)
                exit(2)
            }
            guard let display = content.displays.first else {
                fputs("No display is available for audio capture\n", stderr)
                exit(3)
            }

            let filter = SCContentFilter(
                display: display,
                including: [spotify],
                exceptingWindows: []
            )
            let configuration = SCStreamConfiguration()
            configuration.capturesAudio = true
            configuration.excludesCurrentProcessAudio = true
            configuration.sampleRate = 48_000
            configuration.channelCount = 2
            configuration.width = 2
            configuration.height = 2
            configuration.minimumFrameInterval = CMTime(value: 1, timescale: 1)

            let meter = AudioMeter()
            let queue = DispatchQueue(label: "com.federicoweber.ai-macropad.audio-meter")
            let stream = SCStream(filter: filter, configuration: configuration, delegate: meter)
            try stream.addStreamOutput(meter, type: .audio, sampleHandlerQueue: queue)
            try await stream.startCapture()

            while true {
                try await Task.sleep(nanoseconds: 3_600_000_000_000)
            }
        } catch {
            fputs("Spotify audio capture failed: \(error)\n", stderr)
            exit(1)
        }
    }
}
