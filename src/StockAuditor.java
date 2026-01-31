import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class StockAuditor {
    private static final String DB_URL = "jdbc:sqlite:mi-portafolio-inventario/data/inventario.db";
    private static final String QUERY = "SELECT nombre, stock FROM productos WHERE stock <= ?";

    public static void main(String[] args) {
        int umbral = 5;
        if (args.length > 0) {
            try {
                umbral = Integer.parseInt(args[0]);
            } catch (NumberFormatException ex) {
                System.out.println("Umbral invalido. Usando 5 por defecto.");
            }
        }

        StockAuditor auditor = new StockAuditor();
        try {
            Class.forName("org.sqlite.JDBC");
            String report = auditor.generateReport(umbral);
            System.out.print(report);
            auditor.saveReportToFile(report);
        } catch (ClassNotFoundException ex) {
            System.out.println("No se encontro el driver SQLite: " + ex.getMessage());
        } catch (SQLException ex) {
            System.out.println("Error al consultar la base de datos: " + ex.getMessage());
        } catch (IOException ex) {
            System.out.println("Error al guardar el reporte: " + ex.getMessage());
        }
    }

    public String generateReport(int umbral) throws SQLException {
        List<String> rows = new ArrayList<>();
        try (Connection conn = DriverManager.getConnection(DB_URL);
             PreparedStatement stmt = conn.prepareStatement(QUERY)) {
            stmt.setInt(1, umbral);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    String nombre = rs.getString("nombre");
                    int stock = rs.getInt("stock");
                    rows.add(String.format("- %s | stock: %d", nombre, stock));
                }
            }
        }

        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        StringBuilder builder = new StringBuilder();
        builder.append("==============================\n");
        builder.append("ALERTA DE STOCK\n");
        builder.append("Timestamp: ").append(timestamp).append("\n");
        builder.append("Umbral: ").append(umbral).append("\n");
        builder.append("==============================\n");

        if (rows.isEmpty()) {
            builder.append("No hay productos con stock bajo.\n");
        } else {
            for (String row : rows) {
                builder.append(row).append("\n");
            }
        }
        builder.append("\n");
        return builder.toString();
    }

    private void saveReportToFile(String content) throws IOException {
        Path logsDir = Paths.get("logs");
        if (!Files.exists(logsDir)) {
            Files.createDirectories(logsDir);
        }

        Path reportPath = logsDir.resolve("auditoria_stock.txt");
        try (var writer = Files.newBufferedWriter(
                reportPath,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND)) {
            writer.write(content);
        }
    }
}