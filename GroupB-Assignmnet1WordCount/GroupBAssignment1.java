import java.io.*;
import java.util.*;

public class GroupBAssignment1 {
    public static void main(String[] args) {
        String fileName = "input.txt";
        HashMap<String, Integer> wordMap = new HashMap<>();

        try {
            BufferedReader br = new BufferedReader(new FileReader(fileName));
            String line;

            while ((line = br.readLine()) != null) {
                // Convert to lowercase and remove punctuation
                line = line.toLowerCase().replaceAll("[^a-z ]", "");
                String[] words = line.split("\\s+");

                for (String word : words) {
                    if (word.isEmpty()) continue;

                    wordMap.put(word, wordMap.getOrDefault(word, 0) + 1);
                }
            }

            br.close();

            System.out.println("Word Count Result:");
            for (Map.Entry<String, Integer> entry : wordMap.entrySet()) {
                System.out.println(entry.getKey() + " : " + entry.getValue());
            }
        } catch (Exception e) {
            System.out.println("Error: " + e);
        }
    }
}


