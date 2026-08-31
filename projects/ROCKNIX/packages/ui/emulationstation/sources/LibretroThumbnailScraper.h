#pragma once
#ifndef ES_APP_SCRAPERS_LIBRETRO_THUMBNAIL_SCRAPER_H
#define ES_APP_SCRAPERS_LIBRETRO_THUMBNAIL_SCRAPER_H

#include "scrapers/Scraper.h"

class LibretroThumbnailScraper : public Scraper
{
public:
	void generateRequests(const ScraperSearchParams& params,
		std::queue<std::unique_ptr<ScraperRequest>>& requests,
		std::vector<ScraperSearchResult>& results) override;

	bool isSupportedPlatform(SystemData* system) override;
	const std::set<ScraperMediaSource>& getSupportedMedias() override;
};

class LibretroThumbnailRequest : public ScraperHttpRequest
{
public:
	LibretroThumbnailRequest(std::vector<ScraperSearchResult>& results,
		const std::string& probeUrl, const std::string& gameName,
		const std::string& boxartUrl, const std::string& snapUrl,
		const std::string& titleUrl, const std::string& logoUrl);

protected:
	bool process(const std::string& response,
		std::vector<ScraperSearchResult>& results) override;
	bool retryOn249() override { return false; }

private:
	std::string mGameName;
	std::string mBoxartUrl;
	std::string mSnapUrl;
	std::string mTitleUrl;
	std::string mLogoUrl;
};

#endif
