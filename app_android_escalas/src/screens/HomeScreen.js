import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert, Dimensions } from 'react-native';
import api from '../api';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInUp } from 'react-native-reanimated';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const [escalas, setEscalas] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEscalas = async () => {
    try {
      const response = await api.get('/escalas/');
      setEscalas(response.data);
    } catch (error) {
      console.log('Erro ao buscar escalas', error);
      Alert.alert('Erro', 'Não foi possível carregar as escalas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalas();
  }, []);

  const renderItem = ({ item, index }) => (
    <Animated.View entering={FadeInUp.delay(index * 100).springify()}>
      <LinearGradient
        colors={['rgba(31, 41, 55, 0.8)', 'rgba(17, 24, 39, 0.9)']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        <View style={styles.glassHighlight} />
        <View style={styles.headerRow}>
          <View style={styles.dateBadge}>
            <Text style={styles.dateText}>{item.data_escala}</Text>
          </View>
          <Text style={styles.timeText}>{item.horario_inicio} às {item.horario_fim}</Text>
        </View>
        <Text style={styles.evento}>{item.tipo_evento_display}</Text>
        <View style={styles.footerRow}>
          <Text style={styles.depto}>{item.departamento_nome}</Text>
          <View style={styles.funcaoBadge}>
            <Text style={styles.funcaoText}>{item.funcao_nome}</Text>
          </View>
        </View>
      </LinearGradient>
    </Animated.View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['rgba(59, 130, 246, 0.1)', 'transparent']}
        style={styles.backgroundGlow}
      />
      <Text style={styles.title}>Minhas Próximas Escalas</Text>
      {loading ? (
        <ActivityIndicator size="large" color="#60a5fa" style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={escalas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 100, paddingTop: 10 }}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={<Text style={styles.empty}>Nenhuma escala programada.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', paddingHorizontal: 20 },
  backgroundGlow: { position: 'absolute', top: 0, left: 0, right: 0, height: 300 },
  title: { fontSize: 28, fontWeight: '900', color: '#f8fafc', marginBottom: 20, marginTop: 50, letterSpacing: -0.5 },
  card: {
    padding: 18,
    borderRadius: 20,
    marginBottom: 16,
    borderColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    overflow: 'hidden',
    shadowColor: '#000', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.3, shadowRadius: 15, elevation: 10
  },
  glassHighlight: { position: 'absolute', top: 0, left: 0, right: 0, height: '40%', backgroundColor: 'rgba(255,255,255,0.02)' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12, alignItems: 'center' },
  dateBadge: { backgroundColor: 'rgba(59, 130, 246, 0.15)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10, borderWidth: 1, borderColor: 'rgba(59, 130, 246, 0.3)' },
  dateText: { color: '#60a5fa', fontWeight: '800', fontSize: 13, letterSpacing: 0.5 },
  timeText: { color: '#94a3b8', fontSize: 12, fontWeight: '600' },
  evento: { fontSize: 20, fontWeight: '800', color: '#f1f5f9', marginBottom: 15, letterSpacing: -0.3 },
  footerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  depto: { color: '#cbd5e1', fontSize: 14, fontWeight: '500' },
  funcaoBadge: { backgroundColor: 'rgba(0,0,0,0.3)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.05)' },
  funcaoText: { color: '#94a3b8', fontSize: 12, fontWeight: '700' },
  empty: { color: '#64748b', fontSize: 16, textAlign: 'center', marginTop: 40, fontWeight: '500' }
});
