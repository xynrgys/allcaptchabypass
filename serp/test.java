class test{
    public static int findCharacterIndex(String test, String target, int[] array){
        //Write your code here (return the index where the string matches the target)
        StringBuilder temp = new StringBuilder();
        temp.append(test);
        for (int n : array){
            temp.deleteCharAt(n - 1);
            String check = temp.toString();
            if(check.equals(target)){
                return n;
            }
        }
        return 0;
    }
    public static void main(String[] args) {
        String test = "hbkdi";
        String target = "bd";
        int[] array = new int[] {5, 1, 3, 2, 4};
        System.out.println(findCharacterIndex(test, target, array));
    }
}