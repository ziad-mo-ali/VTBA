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
    private static final Method TO_FLOAT_VECTOR_METHOD;
    private static final Method CLOSE_METHOD;

    static {
        Class<?> nd4jClass = null;
        Method createArrayMethod = null;
        Method createMatrixMethod = null;
        Method mmulMethod = null;
        Method reshapeMethod = null;
        Method getFloatMethod = null;
        Method toFloatVectorMethod = null;
        Method closeMethod = null;
        boolean available = false;
        try {
            nd4jClass = Class.forName("org.nd4j.linalg.factory.Nd4j");
            createArrayMethod = nd4jClass.getMethod("create", float[].class, long[].class);
            createMatrixMethod = nd4jClass.getMethod("create", float[][].class);
            Class<?> indArrayClass = Class.forName("org.nd4j.linalg.api.ndarray.INDArray");
            mmulMethod = indArrayClass.getMethod("mmul", indArrayClass);
            reshapeMethod = indArrayClass.getMethod("reshape", long[].class);
            getFloatMethod = indArrayClass.getMethod("getFloat", long.class);
            try {
                toFloatVectorMethod = indArrayClass.getMethod("toFloatVector");
            } catch (NoSuchMethodException ignored) {
                toFloatVectorMethod = null;
            }
            try {
                closeMethod = indArrayClass.getMethod("close");
            } catch (NoSuchMethodException ignored) {
                closeMethod = null;
            }
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
        TO_FLOAT_VECTOR_METHOD = toFloatVectorMethod;
        CLOSE_METHOD = closeMethod;
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
            return ((Float) GET_FLOAT_METHOD.invoke(array, (long) index)).floatValue();
        } catch (Throwable e) {
            throw new RuntimeException("Failed to read float from ND4J array", e);
        }
    }

    public static float[] toFloatVector(Object array, int expectedLength) {
        if (!AVAILABLE) {
            return null;
        }
        try {
            if (TO_FLOAT_VECTOR_METHOD != null)
                return (float[]) TO_FLOAT_VECTOR_METHOD.invoke(array);
            float[] result = new float[expectedLength];
            for (int i = 0; i < expectedLength; i++)
                result[i] = ((Float) GET_FLOAT_METHOD.invoke(array, (long) i)).floatValue();
            return result;
        } catch (Throwable e) {
            throw new RuntimeException("Failed to copy ND4J array to a float vector", e);
        }
    }

    public static void close(Object array) {
        if (array == null || CLOSE_METHOD == null) {
            return;
        }
        try {
            CLOSE_METHOD.invoke(array);
        } catch (Throwable ignored) {
            // Some ND4J workspaces own array lifetimes; their arrays need no explicit close.
        }
    }
}
