/*
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: app_android_escalas/src/screens/LiderMembrosScreen.js
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
*/
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import api from '../api';

export default function LiderMembrosScreen() {
  const [membros, setMembros] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMembros = async () => {
      try {
        const response = await api.get('/lider/membros/');
        setMembros(response.data);
      } catch (error) {
        console.log(error);
      } finally {
        setLoading(false);
      }
    };
    fetchMembros();
  }, []);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.name}>{item.first_name} {item.last_name}</Text>
      <Text style={styles.email}>{item.email}</Text>
      <View style={{flexDirection: 'row', flexWrap: 'wrap', marginTop: 10}}>
        {item.funcoes && item.funcoes.map(f => (
          <View key={f.id} style={styles.badge}><Text style={styles.badgeText}>{f.nome}</Text></View>
        ))}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Membros do Departamento</Text>
      {loading ? <ActivityIndicator size="large" color="#3b82f6" /> : (
        <FlatList
          data={membros}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          ListEmptyComponent={<Text style={{color: '#9ca3af'}}>Nenhum membro encontrado.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20 },
  card: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12, marginBottom: 15 },
  name: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  email: { color: '#9ca3af', fontSize: 14 },
  badge: { backgroundColor: 'rgba(59, 130, 246, 0.2)', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, marginRight: 5, marginTop: 5 },
  badgeText: { color: '#60a5fa', fontSize: 12 }
});
