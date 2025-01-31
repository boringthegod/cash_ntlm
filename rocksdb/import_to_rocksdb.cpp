#include <iostream>
#include <fstream>
#include <string>
#include <rocksdb/db.h>
#include <rocksdb/options.h>

int main() {
    rocksdb::DB* db;
    rocksdb::Options options;
    options.create_if_missing = true;

    std::string kDBPath = "my_rocksdb";

    rocksdb::Status s = rocksdb::DB::Open(options, kDBPath, &db);
    if (!s.ok()) {
        std::cerr << "Erreur ouverture DB: " << s.ToString() << std::endl;
        return 1;
    }

    std::ifstream infile("ntlmandclearpasswords.txt");
    if (!infile.is_open()) {
        std::cerr << "Impossible d'ouvrir le fichier" << std::endl;
        return 1;
    }

    std::string line;
    while (std::getline(infile, line)) {
        size_t pos = line.find(':');
        if (pos == std::string::npos) {
            continue;
        }

        std::string key = line.substr(0, pos);
        std::string value = line.substr(pos + 1);

        rocksdb::Status put_status = db->Put(rocksdb::WriteOptions(), key, value);
        if (!put_status.ok()) {
            std::cerr << "Erreur insertion key=" << key 
                      << " value=" << value << " : " 
                      << put_status.ToString() << std::endl;
        }
    }

    infile.close();

    delete db;

    std::cout << "Import terminé avec succès !" << std::endl;
    return 0;
}
