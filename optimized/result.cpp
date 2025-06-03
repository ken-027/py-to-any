#include <iostream>
#include <string>
#include <unordered_map>

int main() {
    std::unordered_map<std::string, std::string> person = {
        {"name", "John Doe"},
        {"age", "28"}
    };

    for (const auto& p : person) {
        std::cout << p.first << ": " << p.second << std::endl;
    }

    return 0;
}