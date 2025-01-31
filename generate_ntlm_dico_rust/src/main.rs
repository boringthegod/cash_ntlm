use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use md4::{Md4, Digest};
use hex;


fn ntlm_hash(password: &str) -> String {
    let mut hasher = Md4::new();

    let mut buf = Vec::new();
    for c in password.encode_utf16() {
        buf.push((c & 0xFF) as u8);
        buf.push((c >> 8) as u8);
    }
    hasher.update(&buf);

    let result = hasher.finalize();
    hex::encode(result)
}

fn main() -> std::io::Result<()> {

    let args: Vec<String> = env::args().collect();
    let length: usize = if args.len() > 1 {
        args[1].parse().unwrap_or(3)
    } else {
        3
    };

    let characters = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ\
                       abcdefghijklmnopqrstuvwxyz\
                       0123456789\
                       !@#$%^&*()_+-={}[]|:;'<>,.?/~`\\\"";
    let base = characters.len();
    let total_combinations = base.pow(length as u32);

    println!(
        "Génération de tous les mots de passe de longueur {}, soit {} combinaisons...",
        length, total_combinations
    );

    let file = File::create("ntlm_output.txt")?;
    let mut writer = BufWriter::new(file);

    for i in 0..total_combinations {
        let mut n = i;
        let mut pass_bytes = vec![0u8; length];
        for pos in (0..length).rev() {
            let idx = (n % base) as usize;
            pass_bytes[pos] = characters[idx];
            n /= base;
        }

        let password = String::from_utf8(pass_bytes).unwrap();
        let hash = ntlm_hash(&password);
        writeln!(writer, "{}:{}", hash, password)?;
    }

    writer.flush()?;
    println!("Terminé ! Résultat dans 'ntlm_output.txt'.");
    Ok(())
}
