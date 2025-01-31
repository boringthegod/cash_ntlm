#include <iostream>
#include <fstream>
#include <string>
#include <vector>

#include <rocksdb/db.h>
#include <rocksdb/options.h>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] 
                  << " <path_to_db> <path_to_hashes_file>" << std::endl;
        return 1;
    }

    std::string db_path = argv[1];
    std::string hashes_file = argv[2];

    rocksdb::DB* db = nullptr;
    rocksdb::Options options;
    options.create_if_missing = false;

    rocksdb::Status s = rocksdb::DB::Open(options, db_path, &db);
    if (!s.ok()) {
        std::cerr << "Erreur ouverture DB " << db_path << ": " 
                  << s.ToString() << std::endl;
        return 1;
    }

    std::ifstream infile(hashes_file);
    if (!infile.is_open()) {
        std::cerr << "Impossible d'ouvrir le fichier : " << hashes_file << std::endl;
        delete db;
        return 1;
    }

    std::vector<std::string> keys_str;
    std::string line;
    while (std::getline(infile, line)) {

        if (!line.empty()) {
            keys_str.push_back(line);
        }
    }
    infile.close();

    std::vector<rocksdb::Slice> keys;
    keys.reserve(keys_str.size());
    for (auto &k : keys_str) {
        keys.push_back(rocksdb::Slice(k));
    }

    std::vector<std::string> values(keys.size());

    std::vector<rocksdb::Status> statuses =
        db->MultiGet(rocksdb::ReadOptions(), keys, &values);

    for (size_t i = 0; i < keys.size(); ++i) {
        if (statuses[i].ok()) {
            std::cout << "[FOUND] " << keys[i].ToString() 
                      << " => " << values[i] << std::endl;
        } else if (statuses[i].IsNotFound()) {
        } else {
            std::cerr << "[ERROR] " << keys[i].ToString() 
                      << " : " << statuses[i].ToString() << std::endl;
        }
    }

    delete db;

    return 0;
}
