package main;

import java.lang.reflect.Method;

public final class Nd4jUtils {
    private static final boolean AVAILABLE;
    private static final Class<?> ND4J_CLASS;
    private static final Method CREATE_ARRAY_METHOD;
    private static final Method CREATE_MATRIX_METHOD;
    private static final Method MMUL_METHOD;
    private static final Method RESHAPE_METHOD;
    private static final Method GET_FLOAT_METHOD;

    static {
        Class<?> nd4jClass = null;
        Method createArrayMethod = null;
        Method createMatrixMethod = null;
        Method mmulMethod = null;
        Method reshapeMethod = null;
        Method getFloatMethod = null;
        boolean available = false;
        try {
            nd4jClass = Class.forName("org.nd4j.linalg.factory.Nd4j");
            createArrayMethod = nd4jClass.getMethod("create", float[].class, long[].class);
            createMatrixMethod = nd4jClass.getMethod("create", float[][].class);
            Class<?> indArrayClass = Class.forName("org.nd4j.linalg.api.ndarray.INDArray");
            mmulMethod = indArrayClass.getMethod("mmul", indArrayClass);
            reshapeMethod = indArrayClass.getMethod("reshape", long[].class);
            getFloatMethod = indArrayClass.getMethod("getFloat", int.class);
            available = true;
        } catch (Throwable ignored) {
            available = false;
        }
        AVAILABLE = available;
        ND4J_CLASS = nd4jClass;
        CREATE_ARRAY_METHOD = createArrayMethod;
        CREATE_MATRIX_METHOD = createMatrixMethod;
        MMUL_METHOD = mmulMethod;
        RESHAPE_METHOD = reshapeMethod;
        GET_FLOAT_METHOD = getFloatMethod;
    }

    private Nd4jUtils() {
    }

    public static boolean isAvailable() {
        return AVAILABLE;
    }

    public static Object create(float[] data, long[] shape) {
        if (!AVAILABLE) {
            return null;
        }
        try {
            return CREATE_ARRAY_METHOD.invoke(null, data, shape);
        } catch (Throwable e) {
            throw new RuntimeException("Failed to create ND4J array", e);
        }
    }

    public static Object create(float[][] data) {
        if (!AVAILABLE) {
            return null;
        }
        try {
            return CREATE_MATRIX_METHOD.invoke(null, new Object[] {data});
        } catch (Throwable e) {
            throw new RuntimeException("Failed to create ND4J matrix", e);
        }
    }

    public static Object mmul(Object matrix, Object vector) {
        if (!AVAILABLE) {
            return null;
        }
        try {
            return MMUL_METHOD.invoke(matrix, vector);
        } catch (Throwable e) {
            throw new RuntimeException("Failed to multiply ND4J arrays", e);
        }
    }

    public static Object reshape(Object array, long[] shape) {
        if (!AVAILABLE) {
            return null;
        }
        try {
            return RESHAPE_METHOD.invoke(array, new Object[] {shape});
        } catch (Throwable e) {
            throw new RuntimeException("Failed to reshape ND4J array", e);
        }
    }

    public static float getFloat(Object array, int index) {
        if (!AVAILABLE) {
            return 0f;
        }
        try {
            return ((Float) GET_FLOAT_METHOD.invoke(array, index)).floatValue();
        } catch (Throwable e) {
            throw new RuntimeException("Failed to read float from ND4J array", e);
        }
    }
}
