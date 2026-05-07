package GroupBAssignment2;

import java.io.*;

public class GroupBAssignment2 {
    public static void main(String[] args) {
        String fileName = "sample_weather.txt";
        double tempSum = 0, dewSum = 0, windSum = 0;
        int count = 0;

        try {
            BufferedReader br = new BufferedReader(new FileReader(fileName));
            String line;

            br.readLine(); // skip header

            while ((line = br.readLine()) != null) {
                String[] data = line.split(",");
                double temp = Double.parseDouble(data[1]);
                double dew = Double.parseDouble(data[2]);
                double wind = Double.parseDouble(data[3]);

                tempSum += temp;
                dewSum += dew;
                windSum += wind;
                count++;
            }

            br.close();

            System.out.println("Average Temperature: " + (tempSum / count));
            System.out.println("Average Dew Point: " + (dewSum / count));
            System.out.println("Average Wind Speed: " + (windSum / count));
        } catch (Exception e) {
            System.out.println("Error: " + e);
        }
    }
}
