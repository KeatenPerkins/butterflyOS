#include "scrapers/LibretroThumbnailScraper.h"

#include "FileData.h"
#include "Log.h"
#include "Settings.h"
#include "SystemData.h"
#include "utils/FileSystemUtil.h"
#include "utils/StringUtil.h"

#include <map>

namespace
{
const std::map<std::string, std::string> SYSTEM_NAMES = {
	{"3do", "The 3DO Company - 3DO"},
	{"amiga", "Commodore - Amiga"}, {"amigacd32", "Commodore - Amiga CD32"},
	{"amstradcpc", "Amstrad - CPC"}, {"arcade", "MAME"},
	{"atari2600", "Atari - 2600"}, {"atari5200", "Atari - 5200"},
	{"atari7800", "Atari - 7800"}, {"atari800", "Atari - 8-bit"},
	{"atarijaguar", "Atari - Jaguar"}, {"atarilynx", "Atari - Lynx"},
	{"atarist", "Atari - ST"}, {"c64", "Commodore - 64"},
	{"channelf", "Fairchild - Channel F"}, {"colecovision", "Coleco - ColecoVision"},
	{"dreamcast", "Sega - Dreamcast"}, {"famicom", "Nintendo - Nintendo Entertainment System"},
	{"fbn", "FBNeo - Arcade Games"}, {"fds", "Nintendo - Family Computer Disk System"},
	{"gameandwatch", "Nintendo - Game & Watch"}, {"gamecube", "Nintendo - GameCube"},
	{"gamegear", "Sega - Game Gear"}, {"gb", "Nintendo - Game Boy"},
	{"gba", "Nintendo - Game Boy Advance"}, {"gbc", "Nintendo - Game Boy Color"},
	{"genesis", "Sega - Mega Drive - Genesis"}, {"intellivision", "Mattel - Intellivision"},
	{"mame", "MAME"}, {"mastersystem", "Sega - Master System - Mark III"},
	{"megacd", "Sega - Mega-CD - Sega CD"}, {"megadrive", "Sega - Mega Drive - Genesis"},
	{"megadrive-japan", "Sega - Mega Drive - Genesis"},
	{"msx", "Microsoft - MSX"}, {"msx2", "Microsoft - MSX2"},
	{"n64", "Nintendo - Nintendo 64"}, {"nds", "Nintendo - Nintendo DS"},
	{"neocd", "SNK - Neo Geo CD"}, {"neogeo", "SNK - Neo Geo"},
	{"nes", "Nintendo - Nintendo Entertainment System"},
	{"ngp", "SNK - Neo Geo Pocket"}, {"ngpc", "SNK - Neo Geo Pocket Color"},
	{"odyssey2", "Magnavox - Odyssey2"}, {"pcengine", "NEC - PC Engine - TurboGrafx 16"},
	{"pcenginecd", "NEC - PC Engine CD - TurboGrafx-CD"}, {"pcfx", "NEC - PC-FX"},
	{"pokemini", "Nintendo - Pokemon Mini"}, {"ps2", "Sony - PlayStation 2"},
	{"psp", "Sony - PlayStation Portable"}, {"psx", "Sony - PlayStation"},
	{"satellaview", "Nintendo - Satellaview"}, {"saturn", "Sega - Saturn"},
	{"scummvm", "ScummVM"}, {"sega32x", "Sega - 32X"},
	{"segacd", "Sega - Mega-CD - Sega CD"},
	{"sfc", "Nintendo - Super Nintendo Entertainment System"},
	{"sg-1000", "Sega - SG-1000"}, {"snes", "Nintendo - Super Nintendo Entertainment System"},
	{"supergrafx", "NEC - PC Engine SuperGrafx"}, {"tg16", "NEC - PC Engine - TurboGrafx 16"},
	{"tg16cd", "NEC - PC Engine CD - TurboGrafx-CD"}, {"vectrex", "GCE - Vectrex"},
	{"virtualboy", "Nintendo - Virtual Boy"}, {"wii", "Nintendo - Wii"},
	{"wonderswan", "Bandai - WonderSwan"}, {"wonderswancolor", "Bandai - WonderSwan Color"},
	{"x68000", "Sharp - X68000"}, {"zx81", "Sinclair - ZX 81"},
	{"zxspectrum", "Sinclair - ZX Spectrum"}
};

std::string safeThumbnailName(std::string name)
{
	// These characters are replaced by underscores by the Libretro database.
	for (char& value : name)
		if (std::string("&*/:`<>?\\|\"").find(value) != std::string::npos)
			value = '_';
	return name;
}

std::string mediaUrl(const std::string& system, const std::string& media,
	const std::string& game)
{
	return "https://thumbnails.libretro.com/" + HttpReq::urlEncode(system) + "/" +
		media + "/" + HttpReq::urlEncode(safeThumbnailName(game)) + ".png";
}

std::string selectedImageUrl(const std::string& source, const std::string& boxart,
	const std::string& snap, const std::string& title)
{
	if (source == "box-2D") return boxart;
	if (source == "sstitle") return title;
	return snap;
}
}

void LibretroThumbnailScraper::generateRequests(const ScraperSearchParams& params,
	std::queue<std::unique_ptr<ScraperRequest>>& requests,
	std::vector<ScraperSearchResult>& results)
{
	auto found = SYSTEM_NAMES.find(params.system->getName());
	if (found == SYSTEM_NAMES.end())
		return;

	std::string gameName = params.nameOverride.empty()
		? Utils::FileSystem::getStem(params.game->getPath()) : params.nameOverride;
	std::string boxart = mediaUrl(found->second, "Named_Boxarts", gameName);
	std::string snap = mediaUrl(found->second, "Named_Snaps", gameName);
	std::string title = mediaUrl(found->second, "Named_Titles", gameName);
	std::string logo = mediaUrl(found->second, "Named_Logos", gameName);

	std::string probe = selectedImageUrl(
		Settings::getInstance()->getString("ScrapperImageSrc"), boxart, snap, title);
	requests.push(std::unique_ptr<ScraperRequest>(new LibretroThumbnailRequest(
		results, probe, params.game->getName(), boxart, snap, title, logo)));
}

bool LibretroThumbnailScraper::isSupportedPlatform(SystemData* system)
{
	return system && SYSTEM_NAMES.find(system->getName()) != SYSTEM_NAMES.end();
}

const std::set<Scraper::ScraperMediaSource>& LibretroThumbnailScraper::getSupportedMedias()
{
	static std::set<ScraperMediaSource> media = {
		ScraperMediaSource::Screenshot, ScraperMediaSource::Box2d,
		ScraperMediaSource::TitleShot, ScraperMediaSource::Wheel
	};
	return media;
}

LibretroThumbnailRequest::LibretroThumbnailRequest(
	std::vector<ScraperSearchResult>& results, const std::string& probeUrl,
	const std::string& gameName, const std::string& boxartUrl,
	const std::string& snapUrl, const std::string& titleUrl,
	const std::string& logoUrl)
	: ScraperHttpRequest(results, probeUrl), mGameName(gameName),
	  mBoxartUrl(boxartUrl), mSnapUrl(snapUrl), mTitleUrl(titleUrl), mLogoUrl(logoUrl)
{
}

bool LibretroThumbnailRequest::process(const std::string&,
	std::vector<ScraperSearchResult>& results)
{
	ScraperSearchResult result("RetroArch Thumbnails");
	result.mdl.set(MetaDataId::Name, mGameName);

	std::string imageSource = Settings::getInstance()->getString("ScrapperImageSrc");
	if (!imageSource.empty())
		result.urls[MetaDataId::Image] = ScraperSearchItem(
			selectedImageUrl(imageSource, mBoxartUrl, mSnapUrl, mTitleUrl), ".png");

	if (!Settings::getInstance()->getString("ScrapperThumbSrc").empty() && imageSource != "box-2D")
		result.urls[MetaDataId::Thumbnail] = ScraperSearchItem(mBoxartUrl, ".png");

	if (!Settings::getInstance()->getString("ScrapperLogoSrc").empty())
		result.urls[MetaDataId::Marquee] = ScraperSearchItem(mLogoUrl, ".png");

	if (Settings::getInstance()->getBool("ScrapeTitleShot") && imageSource != "sstitle")
		result.urls[MetaDataId::TitleShot] = ScraperSearchItem(mTitleUrl, ".png");

	results.push_back(result);
	return true;
}
