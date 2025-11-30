package com.hypertv0.hypert

import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.ExtractorLink
import com.lagradost.cloudstream3.plugins.Plugin
import com.lagradost.cloudstream3.plugins.MainAPI
import com.lagradost.cloudstream3.plugins.CloudstreamPlugin
import android.content.Context

@CloudstreamPlugin
class HyperTPlugin: Plugin() {
    override fun load(context: Context) {
        registerMainAPI(HyperTProvider())
    }
}

class HyperTProvider : MainAPI() {
    // Python scriptinin ana dizine çıkardığı dosya
    override var mainUrl = "https://raw.githubusercontent.com/hypertv0/hypert/main/playlist.m3u"
    override var name = "HyperT"
    override val supportedTypes = setOf(TvType.LiveTv)
    override var lang = "tr"
    override val hasMainPage = true

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse? {
        try {
            val response = app.get(mainUrl).text
            val channels = parseM3U(response)
            return newHomePageResponse(HomePageList("Canlı Yayınlar", channels, true))
        } catch (e: Exception) {
            return null
        }
    }

    override suspend fun search(query: String): List<SearchResponse> {
        try {
            val response = app.get(mainUrl).text
            val channels = parseM3U(response)
            return channels.filter { it.name.contains(query, ignoreCase = true) }
        } catch (e: Exception) {
            return emptyList()
        }
    }

    override suspend fun load(url: String): LoadResponse {
        return LiveStreamLoadResponse(
            name = name,
            url = url,
            apiName = this.name,
            dataUrl = url,
            posterUrl = null,
            plot = "trgoal"
        )
    }

    override suspend fun loadLinks(data: String, isCasting: Boolean, subtitleCallback: (SubtitleFile) -> Unit, callback: (ExtractorLink) -> Unit): Boolean {
        callback.invoke(
            ExtractorLink(
                source = name,
                name = name,
                url = data,
                referer = "https://trgoals.xyz/",
                quality = 0,
                isM3u8 = true
            )
        )
        return true
    }

    private fun parseM3U(content: String): List<LiveSearchResponse> {
        val list = mutableListOf<LiveSearchResponse>()
        val lines = content.lines()
        var title = ""
        for (line in lines) {
            val l = line.trim()
            if (l.startsWith("#EXTINF:")) {
                title = l.substringAfterLast(",").trim()
            } else if (l.isNotEmpty() && !l.startsWith("#") && title.isNotEmpty()) {
                list.add(LiveSearchResponse(title, l, this.name, TvType.LiveTv, null))
                title = ""
            }
        }
        return list
    }
}
