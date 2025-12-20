public class InefficientString {
    public static void main(String[] args) {
        String str = "";
        // Inefficient: concatenating in a loop creates many intermediate strings
        for(int i = 0; i < 5; i++) {
            str += "Hello";
        }
        System.out.println(str);
    }
}
