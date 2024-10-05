import Slider from "@react-native-community/slider";
import { CameraView, Camera } from "expo-camera/next";
import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Button, Text } from "react-native-paper";
import { TransferSolModal } from "../components/account/account-ui";
import {
  clusterApiUrl,
  Connection,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionMessage,
  VersionedTransaction,
} from "@solana/web3.js";
import { useTransferSol } from "../components/account/account-data-access";
import { useAuthorization } from "../utils/useAuthorization";
import { transact } from "@solana-mobile/mobile-wallet-adapter-protocol-web3js";
import { useConnection } from "../utils/ConnectionProvider";
import { ConnectButton } from "../components/sign-in/sign-in-ui";
export default function BlankScreen() {
  const [hasPermission, setHasPermission] = useState<any>(null);
  const [scanned, setScanned] = useState(false);
  const [solanaAddress, setSolanaAddress] = useState("");
  const [deviceID, setDeviceID] = useState("");
  const [time, setTime] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const { selectedAccount } = useAuthorization();
  useEffect(() => {
    const getCameraPermissions = async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
    };

    getCameraPermissions();
  }, []);
  const handleBarcodeScanned = ({ type, data }: any) => {
    setScanned(true);
    console.log(data);
    // alert(`${data}`);
    // check if data has : and split it
    const splitData = data.split(":");
    // check if the split data is more than 2
    if (splitData.length < 2) {
      alert("Invalid QR Code");
      return;
    }

    const data2 = splitData[1].split("?");
    const solanaAddress = data2[0];
    const data3 = data2[1].split("&");
    const deviceID = data3[2].split("=")[1];
    const amount = data3[0].split("=")[1];
    let time = "15";
    if (amount === "0.01") {
      time = "15";
    }
    if (amount === "0.02") {
      time = "30";
    }
    if (amount === "0.03") {
      time = "45";
    }
    if (amount === "0.04") {
      time = "60";
    }
    if (amount === "0.05") {
      time = "75";
    }
    if (amount === "0.06") {
      time = "90";
    }
    if(amount === "0.07") {
      time = "105";
    }
    if(amount === "0.08") {
      time = "120";
    }


    // check if solana address is valid
    if (solanaAddress.length !== 44) {
      alert("Invalid Solana Address");
      return;
    }

    // check if deviceID is valid its is like device223
    if ("device" !== deviceID.slice(0, 6)) {
      alert("Invalid Device ID");
      return;
    }

    // check if time is valid its in in minutes like 30, 60, 90
    if (isNaN(parseInt(time))) {
      alert("Invalid Time");
      return;
    }

    // alert("Valid QR Code");

    setSolanaAddress(solanaAddress);
    setDeviceID(deviceID);
    setTime(time);
    setShowModal(true);
  };

  if (hasPermission === null) {
    return <Text>Requesting for camera permission</Text>;
  }
  if (hasPermission === false) {
    return <Text>No access to camera</Text>;
  }

  return (
    <View style={styles.screenContainer}>
      {showModal && (
        <View
          style={{
            backgroundColor: "white",
            padding: 16,
            paddingVertical: 44,
            borderRadius: 8,
            elevation: 8,
            position: "absolute",
            top: 50,
            left: 16,
            right: 16,
            zIndex: 100,
          }}
        >
          <Text
            style={{
              fontWeight: "bold",
              fontSize: 18,
              marginBottom: 16,
              color: "black",
            }}
          >
            Device ID: {solanaAddress.slice(0, 14)}...
          </Text>

          <View style={{ flexDirection: "row", alignItems: "center" }}>
            <Slider
              style={{ width: 200, height: 40 }}
              minimumValue={15}
              maximumValue={120}
              step={15}
              value={parseInt(time)}
              onValueChange={(value) => {
                // use only time like 15, 30, 45, 60, 75, 90, 120
                if (value < 15) {
                  value = 15;
                }
                if (value < 30) {
                  value = 30;
                }
                if (value < 45) {
                  value = 45;
                }
                if (value < 60) {
                  value = 60;
                }
                if (value < 75) {
                  value = 75;
                }
                if (value < 90) {
                  value = 90;
                }
                if (value < 120) {
                  value = 120;
                }
              }}
              minimumTrackTintColor="#1EB1FC"
              maximumTrackTintColor="#1EB1FC"
              thumbTintColor="#1EB1FC"
            />
            <Text
              style={{
                color: "black",
                marginLeft: 8,
              }}
            >
              Time: {time} min
            </Text>
          </View>
          {selectedAccount && (
            <TransferButton
              address={selectedAccount.publicKey}
              destinationAddress={new PublicKey(solanaAddress)}
              time={time}
              setShowModal={setShowModal}
              deviceID={deviceID}
            />
          )}
          {
            !selectedAccount && (
              <ConnectButton />
            )
          }
        </View>
      )}
      <CameraView
        onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
        barcodeScannerSettings={{
          barcodeTypes: ["qr", "pdf417"],
        }}
        style={StyleSheet.absoluteFillObject}
      />

      {scanned && (
        <Button
          mode="contained"
          style={{
            marginTop: 16,
            position: "absolute",
            bottom: 16,
            left: 16,
            right: 16,
          }}
          onPress={() => setScanned(false)}
        >
          <Text style={{ color: "black" }}>Scan Again</Text>
        </Button>
      )}
    </View>
  );
}

const TransferButton = ({
  address,
  destinationAddress,
  time,
  deviceID,
  setShowModal,
}: {
  address: PublicKey;
  destinationAddress: PublicKey;
  time: string;
  deviceID: string;
  setShowModal: (value: boolean) => void;
}) => {
  const authorisation = useAuthorization();
  const transferSol = useTransferSol({ address });
  const { authorizeSessionWithSignIn, authorizeSession, deauthorizeSession } =
    useAuthorization();
  const { connection } = useConnection();
  return (
    <Button
      mode="contained"
      onPress={async () => {
        let lamports = 0;
        if (time === "15") {
          lamports = 10_000_000
        }
        if (time === "30") {
          lamports = 20_000_000
        }
        if (time === "45") {
          lamports = 30_000_000
        }
        if (time === "60") {
          lamports = 40_000_000
        }
        if (time === "75") {
          lamports = 50_000_000
        }
        if (time === "90") {
          lamports =  60_000_000
        }
        if (time === "105") {
          lamports = 70_000_000
        }
        if (time === "120") {
          lamports = 80_000_000
        }
        console.log(
          lamports,
          time,
          destinationAddress.toString(),
          address.toString()
        );
        // transferSol
        //   .mutateAsync({
        //     destination: new PublicKey(destinationAddress),
        //     amount: lamports,
        //   })
        //   .then(() => setShowModal(false));

        const txSignature = await transact(async (wallet) => {
          const result = await authorizeSession(wallet);
          console.log(result);
          const transaction = new Transaction().add(
            SystemProgram.transfer({
              fromPubkey: address,
              toPubkey: destinationAddress,
              lamports: lamports,
            })
          );
          // const signatures = await wallet.signAndSendTransactions({
          //   transactions: [transaction],
          // });
          // console.log(signatures);
          // return  signatures[0];
          const con = new Connection(clusterApiUrl("devnet"), "confirmed");
          const block = await con.getLatestBlockhash();
          const txMessage = new TransactionMessage({
            payerKey: address,
            recentBlockhash: block.blockhash,
            instructions: transaction.instructions,
          }).compileToV0Message();
          const transferTx = new VersionedTransaction(txMessage);

          // Send the unsigned transaction, the wallet will sign and submit it to the network,
          // returning the transaction signature.
          const transactionSignatures = await wallet.signAndSendTransactions({
            transactions: [transferTx],
          });

          return transactionSignatures[0];
        });

        const confirmationResult = await connection.confirmTransaction(
          txSignature,
          "confirmed"
        );

        console.log(confirmationResult);
      }}
    >
      <Text style={{ color: "black" }}>Transfer</Text>
    </Button>
  );
};

const styles = StyleSheet.create({
  screenContainer: {
    height: "100%",
    padding: 16,
  },
});
