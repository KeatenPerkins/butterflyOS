#pragma once

#include <rapidjson/document.h>
#include <rapidjson/prettywriter.h>
#include <rapidjson/stringbuffer.h>

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

namespace ButterflyFavorites
{
static const char* playlistPath = "/storage/playlists/builtin/content_favorites.lpl";

inline bool load(rapidjson::Document& document)
{
	std::ifstream input(playlistPath);
	if (!input)
		return false;

	std::stringstream contents;
	contents << input.rdbuf();
	document.Parse(contents.str().c_str());
	return document.IsObject() && document.HasMember("items") && document["items"].IsArray();
}

inline bool contains(const std::string& path)
{
	rapidjson::Document document;
	if (!load(document))
		return false;

	for (const auto& item : document["items"].GetArray())
		if (item.IsObject() && item.HasMember("path") && item["path"].IsString() &&
			path == item["path"].GetString())
			return true;

	return false;
}

inline bool update(const std::string& path, const std::string& label, bool favorite)
{
	rapidjson::Document document;
	if (!load(document))
	{
		document.SetObject();
		auto& allocator = document.GetAllocator();
		document.AddMember("version", "1.5", allocator);
		document.AddMember("default_core_path", "DETECT", allocator);
		document.AddMember("default_core_name", "DETECT", allocator);
		document.AddMember("label_display_mode", 0, allocator);
		document.AddMember("right_thumbnail_mode", 0, allocator);
		document.AddMember("left_thumbnail_mode", 0, allocator);
		document.AddMember("sort_mode", 0, allocator);
		document.AddMember("items", rapidjson::Value(rapidjson::kArrayType), allocator);
	}

	auto& allocator = document.GetAllocator();
	auto& items = document["items"];
	bool found = false;
	for (auto item = items.Begin(); item != items.End();)
	{
		bool matches = item->IsObject() && item->HasMember("path") &&
			(*item)["path"].IsString() && path == (*item)["path"].GetString();
		if (matches && (!favorite || found))
			item = items.Erase(item);
		else
		{
			found = found || matches;
			++item;
		}
	}

	if (favorite && !found)
	{
		rapidjson::Value item(rapidjson::kObjectType);
		item.AddMember("path", rapidjson::Value(path.c_str(), allocator), allocator);
		item.AddMember("label", rapidjson::Value(label.c_str(), allocator), allocator);
		item.AddMember("core_path", "DETECT", allocator);
		item.AddMember("core_name", "DETECT", allocator);
		item.AddMember("crc32", "00000000|crc", allocator);
		item.AddMember("db_name", "", allocator);
		items.PushBack(item, allocator);
	}

	rapidjson::StringBuffer output;
	rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(output);
	document.Accept(writer);

	std::string temporary = std::string(playlistPath) + ".butterflyos.tmp";
	std::ofstream file(temporary, std::ios::trunc);
	if (!file)
		return false;
	file << output.GetString() << '\n';
	file.close();
	return file.good() && std::rename(temporary.c_str(), playlistPath) == 0;
}
}
