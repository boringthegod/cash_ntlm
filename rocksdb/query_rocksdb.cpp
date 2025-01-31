#include <iostream>
#include <rocksdb/db.h>
#include <rocksdb/options.h>

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <cle_a_chercher>" << std::endl;
        return 1;
    }

    std::string key_to_search = argv[1];

    rocksdb::DB* db;
    rocksdb::Options options;
    options.create_if_missing = false;
    std::string kDBPath = "my_rocksdb";

    rocksdb::Status s = rocksdb::DB::Open(options, kDBPath, &db);
    if (!s.ok()) {
        std::cerr << "Erreur ouverture DB: " << s.ToString() << std::endl;
        return 1;
    }

    std::string value;
    rocksdb::Status get_status = db->Get(rocksdb::ReadOptions(), key_to_search, &value);

    if (get_status.ok()) {
        std::cout << "Valeur pour " << key_to_search << " = " << value << std::endl;
    } else if (get_status.IsNotFound()) {
        std::cout << "Clé " << key_to_search << " introuvable dans la DB." << std::endl;
    } else {
        std::cerr << "Erreur lecture de la clé: " << get_status.ToString() << std::endl;
    }

    delete db;
    return 0;
}

