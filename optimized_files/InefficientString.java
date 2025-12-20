public class InefficientString {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 5; i++) {
            sb.append("Hello");
        }
        String str = sb.toString();
        System.out.println(str);
    }
}