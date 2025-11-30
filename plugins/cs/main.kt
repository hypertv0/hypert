package com.example.cs

import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*

class CSProvider : MainAPI() {
    override var mainUrl = "https://raw.githubusercontent.com/hypertv0/hypert/refs/heads/main/playlist.m3u"
    override var name = "cs"
    override val supportedTypes = setOf(TvType.Live)

    override suspend fun load(url: String): LoadResponse? {
        val text = app.get(mainUrl).text
        val lines = text.split("\n")

        val channels = mutableListOf<LiveStream>()
        var title = ""
        var referer = ""

        for (line in lines) {
            when {
                line.startsWith("#EXTINF") -> {
                    title = line.substringAfter(",").trim()
                }
                line.startsWith("#EXTVLCOPT:http-referrer=") -> {
                    referer = line.substringAfter("=").trim()
                }
                line.startsWith("http") -> {
                    val streamUrl = line.trim()
                    channels.add(LiveStream(title, streamUrl, referer))
                }
            }
        }

        return LiveStreamLoadResponse(name, channels)
    }
}

data class LiveStream(
    val title: String,
    val url: String,
    val referer: String
)

class LiveStreamLoadResponse(
    override val name: String,
    val streams: List<LiveStream>
) : LoadResponse() {
    override val type = TvType.Live
}
